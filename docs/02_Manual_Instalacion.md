# 02 - Manual de Instalación

### Requisitos

- Docker 20+
- Docker Compose 2+
- Puerto libres: 8050 (dashboard), 8080 (Airflow), 5601 (Kibana), 9200 (Elasticsearch)

### Pasos de despliegue

```bash
git clone https://github.com/cbarret276/TFM.git
cd TFM
docker compose up --build
```

### Acceso a servicios

- Dashboard: http://localhost:8050
- Airflow: http://localhost:8080
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601

### Variables y configuración

Ajustes como tokens API se gestionan mediante variables de entorno o ficheros `.env` si se desea extender.
