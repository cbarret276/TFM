from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import requests
from elasticsearch import Elasticsearch, helpers
import ast, os
from concurrent.futures import ThreadPoolExecutor, as_completed

# API params
TRIAGE_API_KEY = os.getenv("TRIAGE_API_KEY")
SIZE_PAGE = 50
TRIAGE_ES_INDEX = "bronze_mw_raw"

if not TRIAGE_API_KEY:
    raise ValueError("Missing TRIAGE_API_KEY environment variable")

# Ingestion params
MAX_DOMAINS = 100  # Maximum number of domains to include
MAX_IPS = 100  # Maximum number of IPs to include

# Index settings and mappings params
INDEX_SETTINGS = {
    "settings": {
        "index": {
            "number_of_shards": 2,
            "sort.field": ["created"],
            "sort.order": ["asc"]
        },
        "mapping": {
            "total_fields.limit": 500,
            "nested_fields.limit": 20,
            "nested_objects.limit": 1000
        },
        "analysis": {}
    },
    "mappings": {
        "properties": {
            "created": {"type": "date"},
            "delivery_method": {"type": "keyword", "ignore_above": 64},
            "domains": {"type": "keyword"},
            "family": {"type": "keyword", "ignore_above": 64},
            "file_size": {"type": "long"},
            "file_type": {"type": "keyword", "ignore_above": 64},
            "id": {"type": "keyword", "ignore_above": 128},
            "ips": {"type": "keyword"},
            "origin_country": {"type": "keyword", "ignore_above": 5},
            "score": {"type": "byte"},
            "sha256": {"type": "keyword", "ignore_above": 128},
            "tags": {"type": "keyword"},
            "ttp": {"type": "keyword"}
        }
    }
}

# Basic DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 5, 1, 0, 0), # days_ago(6)
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG with a 5-minute execution interval
dag = DAG(
    'gen_bronze_mw_raw_index',
    default_args=default_args,
    description='DAG for continuous ingestion of malware data from Triage API without duplication or loss of events',
    catchup=True,
    schedule_interval=timedelta(minutes=5)
)

# Elasticsearch connection setup
def get_elasticsearch_client():
    return Elasticsearch(
        os.getenv("ELASTIC_HOST"),
        http_auth=(os.getenv("ELASTIC_USER"), os.getenv("ELASTIC_PASSWORD")),
        request_timeout=60,  # Request timeout in seconds
        max_retries=5,  # Number of retries on failure
        retry_on_timeout=True  # Retry if timeout occurs
    )

# Function to fetch sample IDs for a dynamic time range
def fetch_sample_ids(**context):
    # Extract time range for query
    data_interval_start = context['data_interval_start'].replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    data_interval_end = context['data_interval_end'].replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        
    # Definir URL y cabeceras
    url = "https://tria.ge/api/v0/search"
    headers = {'Authorization': f"Bearer {TRIAGE_API_KEY}"}
    
    print("Rango consulta: ",f"from:{data_interval_start} to:{data_interval_end}")

    # Parámetros de consulta con el rango de tiempo    
    query = {"query": f"from:{data_interval_start} to:{data_interval_end}",
            "limit": {SIZE_PAGE},
            "offset": 0}

    # Variables for pagination
    next_page = True
    samples = []

    # Realizar la solicitud
    while next_page:
        response = requests.get(url, headers=headers, params=query)

        print("URL Final:", response.url)
    
        if response.status_code == 200:
            data = response.json()
            sample_ids = [entry['id'] for entry in data['data']]
            samples.extend(sample_ids)

            # Check if there is a next page
            if data["next"]:
                query["offset"]=data["next"]
            else:
                next_page = False
        else:
            print(f"Error en la API de búsqueda: {response.status_code}")
            return []

    print("Nº de muestras: ",len(samples))
    return samples  # Return list of sample IDs


# Transform data to the desired schema
def transform_data(data):
    domains, ips, urls, ttp, family = [], [], [], [], []

    if "family" in data.get("analysis", {}):
        family = data.get("analysis").get("family", {})

    if "signatures" in data:
        highest_score_signature = max(data["signatures"], key=lambda x: x.get("score", 0))
        ttp = highest_score_signature.get("ttp", [])

    if "targets" in data and data["targets"] is not None:
        for target in data.get("targets", []):
            iocs = target.get("iocs", {})
            domains.extend(iocs.get("domains", []))
            ips.extend(iocs.get("ips", []))

    #Truncate domains and IPs
    domains = domains[:MAX_DOMAINS]
    ips = ips[:MAX_IPS]

    transformed_data = {
        "family": family,
        "score": data.get("analysis", {}).get("score"),
        "tags": data.get("analysis", {}).get("tags"),
        "created": data.get("sample", {}).get("created"),
        "id": data.get("sample", {}).get("id"),
        "sha256": data.get("sample", {}).get("sha256"),
        "file_size": data.get("sample", {}).get("size"),
        "ttp": ttp,
        "domains": domains,
        "ips": ips
    }

    return transformed_data


# Fetch sample details and store in Elasticsearch
def fetch_sample_details(samples, **context):
    # Configurar conexión a persistencia
    es = get_elasticsearch_client()
    headers = {'Authorization': f"Bearer {TRIAGE_API_KEY}"}

    # Deserializar el string
    samples = ast.literal_eval(samples)
    print("Nº de muestras: ", len(samples))  

    """Checks if the index exists in Elasticsearch and creates it with settings and mappings if not."""
    if not es.indices.exists(index=TRIAGE_ES_INDEX):
        print(f"Creating index '{TRIAGE_ES_INDEX}' with settings and mappings.")
        es.indices.create(index=TRIAGE_ES_INDEX, body=INDEX_SETTINGS)
    else:
        print(f"Index '{TRIAGE_ES_INDEX}' already exists.")

    # Define a generator for actions
    def generate_actions(samples):
        # Create a thread pool to fetch sample details concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_sample = {
                executor.submit(fetch_sample_detail, 
                                sample_id, headers, 
                                es): sample_id for sample_id in samples}
            
            for future in as_completed(future_to_sample):
                sample_id = future_to_sample[future]
                try:
                    result = future.result()
                    if result:  # Solo añadir si no es None
                        yield {
                            "_op_type": "index",  # Adjust based on the operation you want
                            "_index": TRIAGE_ES_INDEX,
                            "_id": result["_id"],  # Assuming result contains "_id"
                            "_source": result["_source"],  # Assuming result contains "_source"
                        }
                except Exception as e:
                    print(f"Error processing sample {sample_id}: {e}")
    

    # Use streaming_bulk to send data to Elasticsearch
    success, failed = 0, 0
    try:
        for ok, action in helpers.streaming_bulk(es, 
                                                 generate_actions(samples),
                                                 chunk_size=100,
                                                 max_chunk_bytes=80 * 1024 * 1024):
            if ok:
                success += 1
    except Exception as e:
        print(f"Error during streaming_bulk execution: {e}")
        raise

    print(f"Successfully updated {success} documents, failed {failed}")

    es.close()

# Function to fetch individual sample detail and prepare for bulk indexing
def fetch_sample_detail(sample_id, headers, es):
    """Fetches and transforms data for a single sample."""
    url = f"https://tria.ge/api/v0/samples/{sample_id}/overview.json"
    response = requests.get(url, headers=headers)

    print("URL Final:", response.url)

    if response.status_code == 200:
        data = response.json()
        print ("Score:", data.get("analysis").get("score"))
        if data.get("analysis", {}).get("score") > 5:
            transformed_data = transform_data(data)
            # Prepare action for bulk insertion
            print("Transformed data:", transformed_data)
            return {
                "_op_type": "index",  # Insert new document
                "_index": TRIAGE_ES_INDEX,
                "_id": sample_id,
                "_source": transformed_data
            }
    else:
        print(f"Error fetching details for sample {sample_id}: {response.status_code}")
        

# Define the tasks using PythonOperator

# Task 1: Fetch sample IDs for the time window
fetch_sample_ids_task = PythonOperator(
    task_id='fetch_sample_ids',
    python_callable=fetch_sample_ids,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# Task 2: Fetch sample details and store them in Elasticsearch
fetch_sample_details_task = PythonOperator(
    task_id='fetch_sample_details',
    python_callable=fetch_sample_details,
    op_args=['{{ ti.xcom_pull(task_ids="fetch_sample_ids") }}'],
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# Define the task execution order
fetch_sample_ids_task >> fetch_sample_details_task
