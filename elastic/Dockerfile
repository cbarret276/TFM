# Use slim image
FROM elasticsearch:8.15.3

# Environment
ENV discovery.type=single-node  \     
    ES_JAVA_OPTS='-Xmx6g -Xms6g -XX:+UseG1GC' \
    xpack.security.enabled=true \
    xpack.security.enrollment.enabled=false \
    http.cors.enabled=true \
    http.cors.allow-origin='http://gunicorn:5173' \
    http.cors.allow-credentials=true \
    http.cors.allow-headers='X-Requested-With, Content-Type, Authorization'
      
# Installs
# RUN apt-get update && apt-get install -y telnet net-tools iputils-ping netcat
