# Use a lightweight Airflow image with Python 3.10
FROM apache/airflow:slim-2.11.0-python3.10

# Install required Python packages and initialize Airflow metadata database
RUN pip install --no-cache-dir psycopg2-binary elasticsearch==7.17.12

# Override the default entrypoint to allow chaining multiple shell commands
ENTRYPOINT ["sh", "-c"]

# Default command: create admin user, then launch scheduler and webserver in background
CMD ["airflow scheduler & airflow webserver"]
