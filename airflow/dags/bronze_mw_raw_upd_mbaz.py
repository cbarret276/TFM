from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import requests
from elasticsearch import Elasticsearch, helpers
import ast, os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Elasticsearch Index Names
BRONZE_INDEX = "bronze_mw_raw" 

# API params for Malware Bazaar
API_KEY = os.getenv("ABUSECH_API_KEY")
URL = "https://mb-api.abuse.ch/api/v1/"

if not API_KEY:
    raise ValueError("Missing ABUSECH_API_KEY environment variable")

# Define the DAG
default_args = {
    'owner': 'airflow',  
    'depends_on_past': False,  
    'start_date': datetime(2025, 5, 1, 0, 0), 
    'email_on_failure': False,  
    'email_on_retry': False,  
    'retries': 3,  
    'retry_delay': timedelta(minutes=1),  
}

dag = DAG(
    'gen_bronze_mw_raw_upd_mbaz',
    default_args=default_args,
    description='DAG to update malware data from Malware Bazaar based on Triage processed data',
    catchup=True,
    schedule_interval=timedelta(minutes=5)
)


# Elasticsearch connection setup
def get_elasticsearch_client():
    return Elasticsearch(
        os.getenv("ELASTIC_HOST"),  # Elasticsearch host URL
        http_auth=(os.getenv("ELASTIC_USER"), os.getenv("ELASTIC_PASSWORD")),
        request_timeout=60,  # Request timeout in seconds
        max_retries=5,  # Number of retries on failure
        retry_on_timeout=True  # Retry if timeout occurs
    )


# Task 0: External Task Sensor to ensure Bronze DAG completion
wait_for_bronze_dag = ExternalTaskSensor(
    task_id="wait_for_bronze_dag",
    external_dag_id="gen_bronze_mw_raw_index",
    external_task_id="fetch_sample_details",
    allowed_states=["success"],
    failed_states=["failed", "skipped"],
    execution_date_fn=lambda dt: dt + timedelta(hours=36),  # Adjust the execution date to check for the last 36 hours      
    mode="reschedule",
    timeout=31 * 365 * 24 * 60 * 60,   # Don`t expire the task
    poke_interval=300, # Time interval to check the sensor state
    dag=dag,
)


# Fetch hashes from Elasticsearch based on processed time windows
def fetch_hashes_from_elastic(**context):
    # Get time window
    start_date = context['data_interval_start'].replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    end_date = context['data_interval_end'].replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    print("Date range: ",f"from:{start_date} to:{end_date}")
    es = get_elasticsearch_client()

    # Query Elasticsearch for hashes within the time window
    query = {
        "_source": ["sha256"],
        "query": {
            "range": {
                "created": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
    }

    results = es.search(index=BRONZE_INDEX, body=query, size=500)

    # Extract hashes from results
    hashes = [{"sha256": hit["_source"]["sha256"], "_id": hit["_id"]} for hit in results['hits']['hits']]
    print("Nº of samples: ",len(hashes))

    es.close()

    return hashes


# Transform the raw API response into the desired format
def transform_data(data, record_id):
    return {
        "_id": record_id,  # Include Elasticsearch _id
        "sha256": data.get("sha256_hash", {}),
        "origin_country": data.get("origin_country", "Unknown"),
        "delivery_method": data.get("delivery_method", "Unknown"),
        "file_type": data.get("file_type", "Unknown")
    }


# Define a function to fetch data for a single hash
def fetch_data(hash_record):
    headers = {'API_KEY': f"{API_KEY}"}
    sha256 = hash_record["sha256"]
    record_id = hash_record["_id"]  # Include _id in the response

    try:
        response = requests.post(
            URL,
            headers=headers,
            data={"query": "get_info", "hash": sha256},
        )
        if response.status_code == 200:
            data = response.json()
            if data['query_status'] == 'ok':
                return transform_data(data['data'][0], record_id)  # Return the first result
    except Exception as e:
        print(f"Error fetching hash {sha256}: {e}")
    return None


# Query Malware Bazaar API for additional information
def query_malware_bazaar(hashes, **context):
    results = []    
    samples = ast.literal_eval(hashes)

    print("Nº de muestras: ", len(samples))
   
    # Use ThreadPoolExecutor to parallelize requests
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Submit tasks for all hashes
        future_to_hash = {executor.submit(fetch_data, hash_record): hash_record for hash_record in samples}

        # Collect results as they complete
        for future in as_completed(future_to_hash):
            result = future.result()
            if result:
                print(result)
                results.append(result)

    print("Nº of samples in mbazaar: ",len(results))
    return results


# Update Elasticsearch with new data from Malware Bazaar
def update_elastic_with_bazaar_data(bazaar_data, **context):
    es = get_elasticsearch_client()

    # Prepare data for bulk update
    actions = []
    bazaar_data = ast.literal_eval(bazaar_data)

    for record in bazaar_data:
        # Add update action
        actions.append({
            "_op_type": "update",
            "_index": BRONZE_INDEX,
            "_id": record.get("_id"),  # Use hash as the ID
            "doc": {
                "origin_country": record.get("origin_country", "Unknown"),
                "delivery_method": record.get("delivery_method", "Unknown"),
                "file_type": record.get("file_type", "Unknown")
            },
            "doc_as_upsert": True  # Add new fields if necessary
        })

    # Perform bulk update
    if actions:
        try:
            print(actions)
            success, failed = helpers.bulk(es, actions, chunk_size=500)
        except helpers.BulkIndexError as e:
            print(f"Bulk update error: {e.errors}")
        print(f"Successfully updated {success} documents, failed {failed}")        
    else:
        print("No documents to update.")


# Task 1: Fetch hashes from Elasticsearch
fetch_hashes_task = PythonOperator(
    task_id='fetch_hashes_from_elastic',
    python_callable=fetch_hashes_from_elastic,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# Task 2: Query Malware Bazaar for additional data
query_bazaar_task = PythonOperator(
    task_id='query_malware_bazaar',
    python_callable=query_malware_bazaar,
    op_args=['{{ ti.xcom_pull(task_ids="fetch_hashes_from_elastic") }}'],  # Pass hashes
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# Task 3: Update Elasticsearch with new data
update_elastic_task = PythonOperator(
    task_id='update_elastic_with_bazaar_data',
    python_callable=update_elastic_with_bazaar_data,
    op_args=['{{ ti.xcom_pull(task_ids="query_malware_bazaar") }}'],  # Pass data
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)


# Define task dependencies
wait_for_bronze_dag >> fetch_hashes_task >> query_bazaar_task >> update_elastic_task
