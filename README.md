# MalwareBI - Cuadro de Mandos para Análisis de Malware

**MalwareBI** es un sistema modular y contenerizado desarrollado como parte de un Trabajo de Fin de Máster en Ciencia de Datos (UNED), orientado al análisis dinámico de amenazas de malware. Captura, enriquece, almacena y visualiza información de ciberinteligencia en tiempo casi real a partir de fuentes abiertas.


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
|  MalwareBazaar| --> | Apache Airflow | --> |   Elasticsearch   |
|  ThreadFox    |     |                |     |                   |
+---------------+     |                |     | (Bronz/Silv/Gold) |
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
| ETL orchestration | Apache Airflow                     |
| Almacenamiento    | Elasticsearch (niveles B/S/G)      |
| Visualización     | Dash Plotly + Bootstrap Components |
| Contenerización   | Docker + Docker Compose            |
| Lenguaje común    | Python 3.10                


---

## 📦 Fuentes de datos integradas

- [x] **Hatching Triage**: Sandbox avanzado de malware.
- [x] **Malware Bazaar**: Repositorio público de muestras.
- [x] **ThreatFox**: Feed de IOCs enriquecidos (IPs, amenazas).

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

## 🗂️ Estructura del repositorio

```plaintext
TFM-main/
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
├── doc/                 # Documentación del proyecto
├── elastic/             # Configuración de índices de Elasticsearch
├── kibana/              # Dashboards o configuraciones de ejemplo
├── docker-compose.yml   # Orquestación de servicios
├── LICENSE              # Licencia del proyecto
└── README.md            # Este documento
```

---

## ⚡ DAGs de Airflow implementados

Están ubicados en la carpeta airflow/dags

- `bronze_mw_raw_idx_triage.py`
- `bronze_mw_raw_upd_mbaz.py`
- `silver_ioc_ip_upd_threatfox.py`
- `gold_malware_agreg_hourly.py`
- `gold_malware_agreg_day.py`

Es necesario crear en la carpeta raíz un fichero `.env`con las claves de las API:

TRIAGE_API_KEY=your_key_here
THREATFOX_API_KEY=your_key_here


---

### Requisitos

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




## 💻 Ejecución local del dashboard (modo desarrollo)

```bash
cd dash_app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python App.py
```

---



## 📄 Licencia

Distribuido bajo licencia MIT.  
Uso académico y formativo. No apto para producción sin revisión de seguridad.

