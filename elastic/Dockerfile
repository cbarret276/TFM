# Usar una imagen base ligera
FROM elasticsearch:8.15.3

# Definir variables de entorno
ENV discovery.type=single-node  \     
    ES_JAVA_OPTS='-Xmx6g -Xms6g -XX:+UseG1GC' \
#    ELASTIC_PASSWORD="elastic"
    xpack.security.enabled=false \
    xpack.security.enrollment.enabled=false \
    http.cors.enabled=true \
    http.cors.allow-origin='http://localhost:5173' \
    http.cors.allow-credentials=true \
    http.cors.allow-headers='X-Requested-With, Content-Type, Authorization'
      
# Installs 
# RUN apt-get update && apt-get install -y telnet net-tools iputils-ping netcat

# Use the official lightweight Elasticsearch image
FROM elasticsearch:8.15.3

# Set environment variables for single-node, memory tuning and CORS settings
# Enables single-node mode (no cluster formation)
ENV discovery.type=single-node \  
    # Allocates 6 GB heap; tune according to host memory
    ES_JAVA_OPTS='-Xmx6g -Xms6g -XX:+UseG1GC' \  
    # Uncomment only if xpack.security is enabled
    #   ELASTIC_PASSWORD="elastic" \  
    # Disables authentication and TLS (for dev purposes only)
    xpack.security.enabled=false \  
    # Disables security auto-enrollment features
    xpack.security.enrollment.enabled=false \  
    # Enables Cross-Origin Resource Sharing
    http.cors.enabled=true \  
    # Allows frontend dev server (e.g., Dash) to access the API
    http.cors.allow-origin='http://localhost:5173' \  
    # Allows cookies/auth headers (safe only with auth in place)
    http.cors.allow-credentials=true \  
     # Common headers allowed in CORS requests
    http.cors.allow-headers='X-Requested-With, Content-Type, Authorization' 

# Optional: install debug tools for container introspection (not recommended in production)
# RUN apt-get update && apt-get install -y telnet net-tools iputils-ping netcat

# --------------------------
# RECOMMENDATIONS:
# --------------------------
# 1. Keep security disabled only in development. In production:
#    - Enable xpack.security.enabled=true
#    - Set a strong ELASTIC_PASSWORD
#    - Use TLS (generate certs via elasticsearch-certutil or enrollment API)
#
# 2. Review Java heap size (ES_JAVA_OPTS):
#    - Xms = Xmx = 50–60% of host memory (but max 31–32 GB)
#    - G1GC is a good default garbage collector for Elasticsearch.
#
# 3. CORS settings:
#    - Keep them tight. In production, allow only known frontend domains.
#    - If not exposing the REST API to a frontend app, disable CORS altogether.
#
# 4. Avoid installing extra packages unless absolutely necessary.
#    - Use a separate debug container or exec into the Elasticsearch one for diagnostics.
#
# 5. Elasticsearch 8+ ships with built-in security. If disabled, expect warnings on startup.
#    - It’s okay for isolated dev environments (e.g., Docker Compose setup for local testing)