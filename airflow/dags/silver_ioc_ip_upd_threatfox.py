from concurrent.futures import ThreadPoolExecutor, as_completed
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch, helpers
import requests
import ast, os

# Generic Constants
BRONZE_INDEX = "bronze_mw_raw"
ENRICHED_IP_INDEX = "silver_ioc_ip_enriched"
THREATFOX_API_KEY = os.getenv("ABUSECH_API_KEY")
THREATFOX_API_URL = "https://threatfox-api.abuse.ch/api/v1/"
ENRICHMENT_TTL_DAYS = 7
HEADERS = {
    "Content-Type": "application/json",
    "Auth-Key": THREATFOX_API_KEY
}

if not THREATFOX_API_KEY:
    raise ValueError("Missing ABUSECH_API_KEY environment variable")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 5, 29, 14), #days_ago(6),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'gen_silver_ioc_ip_threatfox_index',
    default_args=default_args,
    description='Enriquece las IPs observadas con Threatfox y mantiene índice silver',
    schedule_interval=timedelta(minutes=5),
    catchup=True
)

def get_elasticsearch_client():
    return Elasticsearch(["http://elasticsearch:9200"], request_timeout=60)


def parse_first_seen(date_str):
    try:
        if not date_str or date_str.lower() == "null":
            return None
        return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S UTC").isoformat()
    except Exception:
        return None

wait_for_bronze_dag = ExternalTaskSensor(
    task_id="wait_for_bronze",
    external_dag_id="gen_bronze_mw_raw_index",
    external_task_id="fetch_sample_details",
    allowed_states=["success"],
    failed_states=["failed", "skipped"],
    execution_date_fn=lambda dt: dt + timedelta(minutes=10),
    mode="reschedule",
    timeout=31 * 365 * 24 * 60 * 60,
    poke_interval=60,
    dag=dag,
)

def extract_ips_from_bronze(**context):
    start = context['data_interval_start'].isoformat().replace('+00:00', 'Z')
    end = context['data_interval_end'].isoformat().replace('+00:00', 'Z')
    
    print("Rango consulta: ",f"from:{start} to:{end}")

    es = get_elasticsearch_client()
    query = {
        "_source": ["ips"],
        "query": {
            "range": {
                "created": {
                    "gte": start,
                    "lte": end,
                    "format": "strict_date_optional_time"
                }
            }
        }
    }
    results = es.search(index=BRONZE_INDEX, body=query, size=1000)
    ip_set = set()
    for hit in results["hits"]["hits"]:
        for ip in hit["_source"].get("ips", []):
            ip_set.add(ip)
    es.close()
    print(f"IPs encontradas: {len(ip_set)}")
    return list(ip_set)

def enrich_ip(ip, headers, now, ttl_threshold, es):
    
    payload = {
        "query": "search_ioc",
        "search_term": ip
    }

    try:
        r = requests.post(THREATFOX_API_URL, headers=headers, json=payload)
        if r.status_code == 200:
            result = r.json()
            if result.get("query_status") != "ok" or not result.get("data"):
                return None
            
            data = result["data"][0]
            enriched = {
                "ip": ip,
                "last_updated": now,
                "threatfox": {
                    "threat_type": data.get("threat_type"),
                    "malware": data.get("malware"),
                    "malware_printable": data.get("malware_printable"),
                    "confidence_level": data.get("confidence_level"),
                    "first_seen": parse_first_seen(data.get("first_seen")),
                    "ioc_type": data.get("ioc_type"),
                    "reference": data.get("reference")
                }
            }

            print(f"[{ip}] Obtenidos datos de Threatfox con score {data.get('confidence_level')}")
            return {
                "_op_type": "index",
                "_index": ENRICHED_IP_INDEX,
                "_id": ip,
                "_source": enriched
            }
        else:
            print(f"[{ip}] HTTP {r.status_code}")
    except Exception as e:
        print(f"Error enriqueciendo {ip}: {e}")
    return None

def filter_ips_to_enrich(es, ips, ttl_threshold):
    """
    Filters out IPs that are already in the enrichment index and recently updated.
    Only returns IPs that are missing or outdated.
    """
    query = {
        "_source": ["ip", "last_updated"],
        "query": {
            "bool": {
                "must": [
                    {"terms": {"ip": ips}},
                    {"range": {"last_updated": {"gte": ttl_threshold}}}
                ]
            }
        }
    }
    try:
        results = es.search(index=ENRICHED_IP_INDEX, body=query, size=len(ips))
        already_enriched = {hit["_source"]["ip"] for hit in results["hits"]["hits"]}
        to_enrich = list(set(ips) - already_enriched)
        print(f"{len(to_enrich)} IPs necesitan enriquecimiento (de {len(ips)} totales).")
        return to_enrich
    except Exception as e:
        print("Error al filtrar IPs:", e)
        return ips  # fallback: procesar todo si la query falla

def enrich_ips(ips, **context):
    es = get_elasticsearch_client()
    
    if not es.indices.exists(index=ENRICHED_IP_INDEX):
        print(f"Creando índice {ENRICHED_IP_INDEX}")
        mapping = {
            "mappings": {
                "properties": {
                    "ip": {"type": "ip"},
                    "last_updated": {"type": "date"},
                    "threatfox": {
                        "properties": {
                            "threat_type": {"type": "keyword"},
                            "malware": {"type": "keyword"},
                            "malware_printable": {"type": "text"},
                            "confidence_level": {"type": "integer"},
                            "first_seen": {"type": "date"},
                            "ioc_type": {"type": "keyword"},
                            "reference": {"type": "keyword"}
                        }
                    }
                }
            }
        }
        es.indices.create(index=ENRICHED_IP_INDEX, body=mapping)

    now = datetime.now(timezone.utc).isoformat()
    ttl_threshold = (datetime.now(timezone.utc) - timedelta(days=ENRICHMENT_TTL_DAYS)).isoformat()
    
    # Deserialize the IPs from XCom
    ips = ast.literal_eval(ips)
    print("Nº IPs detectadas: ", len(ips))

    # Filter out already updated IPs
    ips = filter_ips_to_enrich(es, ips, ttl_threshold)
    if not ips:
        print("No hay IPs nuevas o desactualizadas para enriquecer.")
        return

    def generate_actions(ips):
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = {executor.submit(enrich_ip, ip, HEADERS, now, ttl_threshold, es): ip for ip in ips}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    print(f"Enriquecido {result}")
                    yield result

    success = 0
    
    try:
        for ok, _ in helpers.streaming_bulk(es, generate_actions(ips), chunk_size=50):
            if ok:
                success += 1
    except helpers.BulkIndexError as e:
        print(f"Bulk update error: {e.errors}")
        raise  # Throw exception for airflow to retry   

    print(f"Enrichment complete: {success} IPs procesadas.")
    es.close() 

extract_ips_task = PythonOperator(
    task_id='extract_ips_from_bronze',
    python_callable=extract_ips_from_bronze,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

enrich_ips_task = PythonOperator(
    task_id='enrich_ips',
    python_callable=enrich_ips,
    provide_context=True,
    op_args=['{{ ti.xcom_pull(task_ids="extract_ips_from_bronze") }}'],
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

wait_for_bronze_dag >> extract_ips_task >> enrich_ips_task