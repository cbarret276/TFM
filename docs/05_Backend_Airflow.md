# 05 - Backend y DAGs en Airflow

### DAGs implementados

- `bronze_mw_raw_idx_triage.py`
- `bronze_mw_raw_upd_mbaz.py`
- `silver_ioc_ip_upd_threatfox.py`
- `gold_malware_agreg_hourly.py`
- `gold_malware_agreg_day.py`

### Optimización aplicada

- Inserciones con `helpers.bulk`
- Paralelización con `ThreadPoolExecutor`
- `ExternalTaskSensor` para dependencias entre DAGs
- Particionado lógico por hora y día

Airflow corre en contenedor dedicado, con interfaz accesible en `http://localhost:8080`.
