# 07 - Enriquecimiento de IPs con ThreatFox

El DAG `silver_ioc_ip_upd_threatfox.py` realiza el enriquecimiento de IPs observadas en muestras recientes.

### Proceso

1. Extrae IPs únicas desde el nivel Bronze.
2. Consulta a ThreatFox (lotes paralelos).
3. Inserta (upsert) resultados en `silver_ioc_ip_enriched`.

### Campos enriquecidos

- `threat_type`, `confidence_level`, `malware`, `ioc_type`, `first_seen`

Esta información es utilizada en visualizaciones como Sankeys, mapas de IPs maliciosas y tablas.
