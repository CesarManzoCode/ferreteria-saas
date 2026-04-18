# ============================================================
# Dockerfile del backend FastAPI
# ============================================================
#
# Usamos imagen slim (no alpine) por dos razones:
#   1. WeasyPrint necesita librerías C que alpine no trae fácil
#   2. psycopg2-binary también necesita librerías del sistema
# slim = Debian mínimo, suficiente para nuestras dependencias
#
FROM python:3.12-slim

# Variables de entorno para Python dentro del contenedor:
#   PYTHONDONTWRITEBYTECODE=1 → no genera archivos .pyc (innecesarios en Docker)
#   PYTHONUNBUFFERED=1 → los prints/logs aparecen en tiempo real sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema operativo
# WeasyPrint necesita: libpango, libcairo, libgdk-pixbuf (para renderizar HTML→PDF)
# build-essential: compilador C para algunas dependencias de Python
# Separamos el apt-get en una sola capa RUN para minimizar capas y tamaño
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements ANTES del código fuente
# Esto aprovecha el cache de Docker: si requirements.txt no cambia,
# Docker no reinstala dependencias aunque cambies el código Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorio para uploads de Excel
RUN mkdir -p /app/uploads

# Puerto que expone el contenedor
EXPOSE 8000

# Script de entrada — maneja migraciones antes de arrancar el servidor
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
