# Dashboard de Análisis de Malware - dash_app

Este módulo contiene la aplicación web desarrollada con Dash y Plotly para visualizar la actividad de malware procesada desde múltiples fuentes. Forma parte del proyecto MalwareBI (TFM en Ciencia de Datos, UNED).

---

## 📊 Funcionalidades

- Vista panorámica: KPIs, histogramas, mapa mundial, treemap táctico.
- MITRE ATT&CK: Visualización de tácticas y técnicas (Sankey, heatmap).
- Indicadores: hashes, IPs, dominios, wordcloud de IOCs.
- Temporal: análisis horario y diario de muestras.
- Geográfico: mapas por origen de amenazas.
- Responsive y multipágina.
- Cambio de tema claro/oscuro con persistencia.
- Filtros globales por fecha, familia, país y tipo.

---

## 📁 Estructura

```plaintext
dash_app/
├── assets/              # Icono, logo, JS y CSS personalizados
├── callbacks/           # Callbacks de interacción por módulo
│   ├── analysis_callbacks.py
│   ├── commons_callbacks.py
│   ├── geolocaltion_callbacks.py
│   ├── home_callbacks.py
│   ├── indicators_callbacks.py
│   └── tactitcs_callbacks.py
├── layouts/             # Componentes visuales como sidebar y navbar
│   ├── dummy_components.py
│   ├── filters.py
│   ├── sidebar.py
│   └── top_navbar.py
├── pages/               # Páginas individuales del dashboard
│   ├── analysis.py
│   ├── geolocation.py
│   ├── home.py
│   ├── indicators.py
│   └── tactics.py
├── utils/               # Funciones auxiliares (fechas, queries a Elasticsearch, etc.)
├── App.py               # Punto de entrada principal
├── app_instance.py      # Inicialización de la app Dash
└── requirements_slim.txt     # Dependencias necesarias
```

---

## 🚀 Ejecución local (sin Docker)

```bash
cd dash_app
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements_slim.txt
python App.py
```

La app estará disponible en: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## ⚙️ Requisitos

- Python 3.10
- Elasticsearch accesible en localhost:9200 (o configurado en `.env` o variables internas)
- Dependencias listadas en `requirements_slim.txt`

---

## 📄 Licencia

Este módulo forma parte del proyecto académico MalwareBI, distribuido bajo licencia MIT.
