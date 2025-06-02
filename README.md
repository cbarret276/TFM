# MalwareBI - Cuadro de Mandos para Análisis de Malware

**MalwareBI** es una solución modular y contenerizada desarrollada como parte de un Trabajo de Fin de Máster en Ciencia de Datos (UNED). Su objetivo es automatizar la recolección, procesamiento y visualización de indicadores de ciberamenazas a partir de fuentes abiertas, facilitando el análisis dinámico de malware en tiempo casi real.


---

# 🎯 Objetivos

- Automatizar la captura periódica de muestras desde APIs públicas de malware.
- Estructurar el procesamiento en flujos ETL orquestados con Airflow.
- Persistir los datos en niveles jerárquicos: Bronze, Silver y Gold.
- Visualizar indicadores clave de forma interactiva, táctica y geográfica.
- Permitir la exploración analítica desde una interfaz responsive y multipágina.


---

## 🧱 Arquitectura del sistema

```plaintext
+---------------+     +----------------+     +-------------------+
|  Triage API   | --> |                |     |                   |
| MalwareBazaar | --> | Apache Airflow | --> |   Elasticsearch   |
|   ThreadFox   |     |                |     |                   |
| MITRE ATT&CK  |     |                |     | (Bronz/Silv/Gold) |
|   Geolite2    |     |     (DAGs)     |     |                   |
+---------------+     |                |     |                   |
                      +----------------+     +-------------------+
                                                      |
                                                      v
                                          +------------------------+
                                          | Dash Plotly Dashboard  |
                                          +------------------------+
```

---

## ⚙️ Tecnologías utilizadas

| Componente        | Tecnología                         |
|-------------------|------------------------------------|
| Orquestación ETL  | Apache Airflow                     |
| Almacenamiento    | Elasticsearch (niveles B/S/G)      |
| Visualización     | Dash Plotly + Bootstrap Components |
| Contenerización   | Docker + Docker Compose            |
| Lenguaje común    | Python 3.10                


---

## 📦 Fuentes de datos integradas

- [x] **Hatching Triage**: Sandbox avanzado de malware.
- [x] **Malware Bazaar**: Repositorio público de muestras.
- [x] **ThreatFox**: Feed de IOCs enriquecidos (IPs, amenazas).
- [x] **MITRE ATT&CK**: Matriz de tácticas, técnicas y procedimientos.
- [x] **Gelolite2 MaxMind**: fuente para geolocalización de IPs.

## 📊 Funcionalidades del dashboard

- 🔍 **Panorámica**: KPIs, top familias, evolución temporal, treemap táctico.
- 🧠 **Tácticas MITRE ATT&CK**: Sankey Táctica→Técnica y Técnica→Familia, heatmaps.
- 🌐 **Geolocalización**: Mapas coropléticos por país, IOCs activos.
- 🧩 **Indicadores (IOCs)**: Wordcloud, top IPs, amenazas asociadas.
- 🧾 **Análisis detallado**: Tabla interactiva filtrable con búsqueda libre.

✅ Responsive (PC, tablet, móvil)  
✅ Cambio de tema claro/oscuro  
✅ Filtros globales por fecha y familia  
✅ Persistencia de sesión y navegación multipágina

---

## 🗂️ Estructura del Repositorio

```plaintext
TFM/
├── airflow/             # DAGs de Airflow para ETL
├── dash_app/            # Aplicación Dash multipágina
│   ├── assets/          # CSS personalizado
│   ├── callbacks/       # Callbacks para cada página o sección
│   ├── layouts/         # Componentes de diseño (sidebar, navbar, temas)
│   ├── pages/           # Páginas del dashboard (panorámica, tácticas, etc.)
│   ├── utils/           # Funciones auxiliares (consultas a Elasticsearch, fechas)
│   ├── App.py           # Punto de entrada principal de la app
│   ├── app_instance.py  # Configuración compartida de la app Dash
│   └── requirements.txt # Dependencias del dashboard
├── docs/                 # Documentación del proyecto
├── elastic/             # Configuración de índices de Elasticsearch
├── gunicorm/            # Seervidor de despliegue de la aplicación
├── kibana/              # Dashboards o configuraciones de ejemplo
├── postgres/            # Base de datos del planificador de Airflow
├── docker-compose.yml   # Orquestación de servicios
├── LICENSE              # Licencia del proyecto
└── README.md            # Este documento
```

---

## ⚡ DAGs de Airflow Implementados

Ubicados en la carpeta `airflow/dags`:

- `bronze_mw_raw_idx_triage.py`
- `bronze_mw_raw_upd_mbaz.py`
- `silver_ioc_ip_upd_threatfox.py`
- `gold_malware_agreg_hourly.py`
- `gold_malware_agreg_day.py`

---

### 🐳 Requisitos y Ejecución

- Docker v20+
- Docker Compose v2+

```bash
git clone https://github.com/cbarret276/TFM.git
cd TFM
docker compose up --build
```

Servicios disponibles:

| Servicio     | URL                          |
|--------------|------------------------------|
| Airflow      | http://localhost:8080        |
| Elasticsearch| http://localhost:9200        |
| Kibana       | http://localhost:5601        |
| Dashboard    | http://localhost:8050        |




## 💻 Ejecución Local del Dashboard (Modo Desarrollo)

```bash
cd dash_app
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.slim.txt
python App.py
```

---


## 📄 Licencia

Distribuido bajo licencia MIT.  
Uso académico y formativo. No apto para producción sin revisión de seguridad.

