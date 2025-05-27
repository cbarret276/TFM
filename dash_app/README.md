# Dashboard de Análisis de Malware - dash_app

Este módulo contiene la aplicación web desarrollada con Dash y Plotly para visualizar la actividad de malware procesada desde múltiples fuentes. Forma parte del proyecto MalwareBI, implementado como parte de un Trabajo de Fin de Máster en Ciencia de Datos (UNED).

---

## 📊 Funcionalidades

- Vista panorámica: KPIs, histogramas, mapa mundial.
- Vista MITRE ATT&CK: tácticas y técnicas mediante treemap.
- Indicadores: dominios, IPs, hashes.
- Visualización temporal: actividad diaria y horaria.
- Visualización geográfica: origen de muestras por país.
- Cambios de tema claro/oscuro (`ThemeChangerAIO`).
- Responsive y multipágina.

---

## 📁 Estructura

```plaintext
dash_app/
├── assets/              # Estilos CSS personalizados
├── callbacks/           # Callbacks de interacción por módulo
│   ├── commons_callbacks.py
│   ├── home_callbacks.py
│   ├── mitre_callbacks.py
│   ├── indicators_callbacks.py
│   ├── geo_callbacks.py
│   └── temporal_callbacks.py
├── layouts/             # Componentes visuales como sidebar y navbar
│   └── sidebar.py
├── pages/               # Páginas individuales del dashboard
│   ├── home.py
│   ├── mitre.py
│   ├── indicators.py
│   ├── geo.py
│   └── temporal.py
├── utils/               # Funciones auxiliares (fechas, queries a Elasticsearch, etc.)
├── App.py               # Punto de entrada principal
├── app_instance.py      # Inicialización de la app Dash
└── requirements.txt     # Dependencias necesarias
```

---

## 🚀 Ejecución local (sin Docker)

```bash
cd dash_app
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python App.py
```

La app estará disponible en: [http://127.0.0.1:8050](http://127.0.0.1:8050)

---

## ⚙️ Requisitos

- Python 3.10
- Elasticsearch accesible en localhost:9200 (o configurado en `.env` o variables internas)
- Dependencias listadas en `requirements.txt`

---

## 📄 Licencia

Este módulo forma parte del proyecto académico MalwareBI, distribuido bajo licencia MIT.
