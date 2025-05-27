# 01 - Arquitectura Técnica

La arquitectura de MalwareBI se compone de varios servicios contenerizados:

- **Airflow**: orquestación de tareas ETL mediante DAGs.
- **Elasticsearch**: almacenamiento documental estructurado en niveles Bronze, Silver y Gold.
- **Dash Plotly**: frontend web para visualización táctica e interactiva.
- **Docker Compose**: despliegue local de servicios.

### Diagrama de arquitectura

El flujo general parte de la captura desde APIs abiertas (Triage, MalwareBazaar, ThreatFox), pasando por enriquecimiento y agregación, hasta su visualización en el dashboard.

    APIs → Airflow → Elasticsearch → Dash UI
