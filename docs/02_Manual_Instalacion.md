# 02 - Manual de Instalación

Este documento describe el proceso de instalación y despliegue de **MalwareBI**, una plataforma contenerizada para el análisis visual de malware, desarrollada como parte de un Trabajo de Fin de Máster en Ciencia de Datos (UNED). La solución se ejecuta de forma local utilizando Docker y Docker Compose.

---

## ✅ Requisitos previos

Antes de instalar el sistema, asegúrese de disponer de lo siguiente:

- **Docker** versión 20 o superior
- **Docker Compose** versión 2 o superior (integrado en Docker Desktop o como plugin)
- **Git** para clonar el repositorio
- Acceso a puertos locales:
  - `5173`: interfaz web del dashboard
  - `8080`: panel de control de Airflow
  - `5601`: acceso a Kibana
  - `9200`: servicio de Elasticsearch

---

## 📦 Clonación y despliegue

Siga los siguientes pasos desde la terminal:

```bash
git clone https://github.com/cbarret276/TFM.git
cd TFM
docker compose up --build
```

Esto descargará el código, construirá las imágenes necesarias y levantará los contenedores definidos en `docker-compose.yml`.

---

## 🌐 Acceso a los servicios desplegados

Una vez iniciado, podrá acceder a los distintos servicios a través del navegador:

| Servicio       | URL                   |
|----------------|------------------------|
| Dashboard      | http://localhost:5173 |
| Airflow        | http://localhost:8080 |
| Elasticsearch  | http://localhost:9200 |
| Kibana         | http://localhost:5601 |

---

## 🔐 Configuración de variables de entorno

Algunos contenedores requieren ficheros de configuración. 

Para Airflow se requiere un fichero `.env_airflow` en la raíz del proyecto con las claves de acceso a APIs externas (Triage, ThreatFox) y la configuación del planificador (paralelismo). 

```.env_airflow
TRIAGE_API_KEY=your_key_here
THREATFOX_API_KEY=your_key_here
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__PARALLELISM=4
AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=8
AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG=4
AIRFLOW__CORE__LOAD_EXAMPLES=False
```

Para la Gunicorn se necesita un fichero `.env_gunicorn` en la raíz del proyecto con la siguiente configuración

```.env_gunicorn
APP_PORT=5173
GUNICORN_RELOAD_ARG="--reload"
ELASTIC_HOST=url_here
```

Para Postgres se necesita un fichero `.env_postgres` en la raíz del proyecto con la siguiente configuración

```.env_postgres
POSTGRES_USER=user_here
POSTGRES_PASSWORD=pass_here
POSTGRES_DB=db_here
```

Estos archivos no se incluye en el repositorio por razones de seguridad. Puedes generar tus claves desde los respectivos portales de las APIs públicas.

---

## ⚙️ Personalización opcional

El fichero `docker-compose.yml` permite modificar puertos, versiones o volúmenes si deseas adaptarlo a entornos específicos.

---

## 🧪 Alternativa: ejecución local para desarrollo

Si solo deseas ejecutar el dashboard puedes hacerlo en modo desarrollo:

```bash
cd dash_app
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python App.py
```

⚠️ Para que funcione correctamente, necesitas tener un servidor Elasticsearch accesible en `localhost:9200` o configurarlo en `app_instance.py`.

---

## ✅ Comprobación

Para verificar que todo funciona:

1. Accede a http://localhost:5173 y comprueba que se carga la interfaz.
2. En Airflow, verifica que los DAGs están disponibles y programados.
3. Comprueba que Kibana se conecta al índice `bronze_mw_raw`.
4. Asegúrate de que los filtros en el dashboard muestran datos reales.

---

Este proceso está diseñado para ser reproducible en cualquier entorno compatible con Docker, sin necesidad de instalación adicional de dependencias ni configuración avanzada.


