# Use a lightweight Airflow image with Python 3.10
FROM apache/airflow:slim-latest-python3.10

# Set environment variables for Airflow configuration
# Use SQLite for local testing (not suitable for production)
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////tmp/airflow.db \  
   # Runs tasks one at a time (simplest executor, good for dev)
    AIRFLOW__CORE__EXECUTOR=SequentialExecutor \  
    # Prevents loading demo DAGs
    AIRFLOW__CORE__LOAD_EXAMPLES=False  

# Install required Python packages and initialize Airflow metadata database
RUN pip install pymongo elasticsearch && airflow db init

# Override the default entrypoint to allow chaining multiple shell commands
ENTRYPOINT ["sh", "-c"]

# Default command: create admin user, then launch scheduler and webserver in background
CMD ["airflow scheduler & airflow webserver"]
