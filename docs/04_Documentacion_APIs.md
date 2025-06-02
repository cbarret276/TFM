 04 - Documentación de APIs

Este documento resume las APIs externas integradas en el sistema **MalwareBI** para la captura periódica y enriquecimiento de datos de malware. Las fuentes seleccionadas permiten disponer de muestras recientes, indicadores de compromiso y metadatos contextuales.

---

## 🌐 APIs integradas

### 🔸 Hatching Triage

- **Descripción**: Sandbox avanzado que analiza muestras cargadas y ofrece informes enriquecidos con comportamiento y clasificación.
- **Método de uso**: Se consulta el endpoint `/search/submissions` mediante una petición GET autenticada.
- **Autenticación**: Mediante cabecera `Authorization: Bearer <token>`
- **Datos utilizados**:
  - `id`: identificador único de la muestra.
  - `score`: nivel de peligrosidad calculado por el motor.
  - `family`: clasificación asignada por el análisis dinámico.
  - `tags`: etiquetas de comportamiento observadas.
  - `ttp`: técnicas MITRE detectadas.

- **Frecuencia de uso**: cada 5min mediante DAG de Airflow (`bronze_mw_raw_idx_triage.py`)

---

### 🔸 Malware Bazaar

- **Descripción**: Repositorio colaborativo que ofrece acceso a muestras de malware con metadatos básicos.
- **Endpoint utilizado**: `/query/get_recent`
- **Método**: POST sin autenticación (API pública)
- **Parámetros**: `selector=100`
- **Datos utilizados**:
  - `sha256`: hash principal.
  - `delivery_method`: vía de propagación (email, exploit, etc).
  - `origin_country`: país estimado de origen de la muestra.

- **Frecuencia de uso**: cada 5min mediante DAG (`bronze_mw_raw_upd_mbaz.py`)

---

### 🔸 ThreatFox

- **Descripción**: API de IOCs enriquecidos publicada por Abuse.ch, incluye IPs, URLs y hashes con contexto.
- **Endpoint**: `/api/v1/`
- **Método**: POST con clave en cuerpo
- **Autenticación**: Clave API proporcionada por el usuario (`THREATFOX_API_KEY`)
- **Datos utilizados**:
  - `ioc`: IP o dominio observado.
  - `malware`: familia relacionada.
  - `confidence_level`: puntuación de fiabilidad.
  - `first_seen`: fecha de detección.
  - `threat_type`: tipo de amenaza (C2, phishing, etc.)

- **Frecuencia de uso**: cada 5min mediante DAG (`silver_ioc_ip_upd_threatfox.py`)

---

## 🧪 Herramientas de prueba

Durante el desarrollo se utilizó [Hoppscotch.io](https://hoppscotch.io) como cliente REST para:

- Validar tokens y autenticaciones (cabecera y cuerpo).
- Probar respuestas JSON y estructura de los objetos.
- Verificar disponibilidad de atributos requeridos.
- Reproducir consultas de forma interactiva sin necesidad de DAGs.

---

## 📄 Formato y validación

Todos los datos recibidos se validan desde la aplicación mediante funciones auxiliares en `utils/`.

---

Este módulo de captura constituye la base del pipeline ETL que alimenta la visualización interactiva y el análisis táctico en el dashboard.
