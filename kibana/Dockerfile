# Use the official Kibana image as base (version must match Elasticsearch)
FROM kibana:8.15.3

# Set environment variables to configure Kibana
ENV ELASTICSEARCH_HOSTS="http://elasticsearch:9200" \
    # Uncomment the following lines if security is enabled
    # ELASTICSEARCH_USERNAME="kibana_system" \
    # ELASTICSEARCH_PASSWORD="your_password" \
    # SERVER_SSL_ENABLED=false \
    # XPACK_SECURITY_ENABLED="true" \

    # Disable Fleet agents (simplifies the setup in development environments)
    xpack.fleet.agents.enabled=false

