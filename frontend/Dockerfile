# ============================================================
# Dockerfile del frontend React
# Multi-stage build: separamos build de producción
# ============================================================
#
# Stage 1 (builder): instala dependencias y compila el React app
# Stage 2 (final):   solo nginx + los archivos estáticos del build
#
# ¿Por qué multi-stage?
#   node_modules pesa ~200-400 MB. La imagen final no necesita
#   node ni npm — solo los archivos HTML/JS/CSS del build.
#   Multi-stage descarta todo el tooling y deja solo lo necesario.
#   Resultado: imagen final de ~25 MB en lugar de ~400 MB.

# ── Stage 1: Build ───────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar package.json primero para aprovechar cache de Docker
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copiar el resto del código y compilar
COPY . .

# VITE_API_URL vacío en build — nginx proxea /api al backend
# En producción, el browser llama a /api/v1/... y nginx lo redirige
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Stage 2: Servidor nginx ──────────────────────────────
FROM nginx:alpine

# Copiar los archivos compilados al directorio de nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración de nginx para SPA (Single Page Application)
# Sin esto, al refrescar /quotes o /catalogs nginx retorna 404
# porque no existe un archivo físico en esa ruta
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
