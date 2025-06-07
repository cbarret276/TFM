
# Manual de Instalación del Sistema

Este documento describe paso a paso cómo instalar y poner en funcionamiento el sistema desde un entorno limpio, basado en Ubuntu Server y utilizando contenedores Docker. Está basado en los comandos ejecutados durante la puesta en marcha del trabajo.

---

## ✅ Requisitos previos

El despliegue del sistema va a requerir lo siguiente:

- **Docker** versión 20 o superior
- **Docker Compose** versión 2 o superior (integrado en Docker Desktop o como plugin)
- **Git** para clonar el repositorio
- Acceso a puertos locales:
  - `5173`: interfaz web del dashboard
  - `8080`: panel de control de Airflow
  - `5601`: acceso a Kibana
  - `9200`: servicio de Elasticsearch


## 🛠️ Instalación de dependencias necesarias

```bash
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### Configurar repositorio oficial de Docker:

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
```

### Instalar Docker y complementos:

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

> Verificar instalación:

```bash
docker --version
docker compose version
```

---

## 📁 Clonación del repositorio y preparación del entorno

```bash
cd /opt
sudo mkdir malwarebi
sudo chown $USER:$USER malwarebi
cd malwarebi

git clone https://github.com/cbarret276/TFM.git .
```

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

## 🔧 3. Despliegue de contenedores

### Construir e iniciar servicios:

```bash
docker compose up --build -d
```

> Comprobar estado:

```bash
docker compose ps
```

---

## 🌬️ Inicialización de Apache Airflow

Acceder al contenedor:

```bash
docker compose exec airflow bash
```

Inicializar base de datos:

```bash
airflow db init
```

Crear usuario administrador:

```bash
airflow users create \
    --username your_data_here \
    --password your_data_here \
    --firstname  \
    --lastname your_data_here \
    --role Admin \
    --email your_data_here
```

Reiniciar el contenedor:

```bash
exit
docker compose restart airflow
```

---

## 📊 5. Comprobación de funcionamiento

Comprobar logs de servicios:

```bash
docker compose logs -f airflow
docker compose logs -f elasticsearch
docker compose ps
```

---


## 🧠 Notas finales

- Si se transfiere una carpeta `data` de otro entorno para Elasticsearch, puede dar errores de permisos: se recomienda limpiarla y permitir que se regenere.


---

## ✅ Servicios por defecto

| Servicio     | URL                        |
|--------------|----------------------------|
| Dashboard    | http://localhost:8050      |
| Airflow      | http://localhost:8080      |
| Elasticsearch| http://localhost:9200      |
| Kibana       | http://localhost:5601      |


## ✅ Comprobación

Para verificar que todo funciona:

1. Accede a http://localhost:5173 y comprueba que se carga la interfaz.
2. En Airflow, verifica que los DAGs están disponibles y programados.
3. Comprueba que Kibana se conecta al índice `bronze_mw_raw`.
4. Asegúrate de que los filtros en el dashboard muestran datos reales.


Este proceso está diseñado para ser reproducible en cualquier entorno compatible con Docker, sin necesidad de instalación adicional de dependencias ni configuración avanzada.


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
