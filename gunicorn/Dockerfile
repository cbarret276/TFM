# Base image optimized for Python 3.12 with Gunicorn
FROM python:3.10.17-alpine3.22

# Dependencys installation
RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY ../dash_app/requirements.slim.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for production
RUN pip install gunicorn

# Arranque dinámico según var GUNICORN_RELOAD_ARG
CMD ["sh", "-c", "gunicorn $GUNICORN_RELOAD_ARG --bind 0.0.0.0:${APP_PORT} App:server"]