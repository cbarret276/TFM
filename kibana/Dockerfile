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

# Optional: install debug tools. This is not recommended for production.
# If needed for troubleshooting in dev, uncomment and rebuild.
# RUN apt-get update && apt-get install -y telnet net-tools iputils-ping netcat

# --------------------------
# RECOMMENDATIONS:
# --------------------------
# 1. Keep this configuration for local or development environments.
# 2. In production:
#    - Enable security (username/password, TLS).
#    - Use secrets for sensitive variables (do not hardcode passwords or keys).
#    - Consider setting up Kibana behind a reverse proxy with HTTPS.
# 3. Avoid installing debugging tools in production containers.
# 4. Ensure the encryption key is unique, 32 bytes (hex) long, and securely stored.
# 5. Validate that the Elasticsearch version matches exactly with Kibana.