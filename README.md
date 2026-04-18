# Ferretería SaaS

Sistema de cotizaciones para ferreterías. Sube tu lista de precios en Excel, busca productos y genera cotizaciones en PDF.

---

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git

Nada más. Docker instala todo lo demás adentro.

---

## Levantar en local (primera vez)

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/ferreteria-saas.git
cd ferreteria-saas
```

### 2. Crear el archivo de variables de entorno

```bash
cp .env.example .env
```

### 3. Generar una SECRET_KEY segura

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y pégalo en el `.env` como valor de `SECRET_KEY`.

El `.env` debe quedar así (cambia los passwords si quieres):

```env
DATABASE_URL=postgresql://ferreteria_user:ferreteria123@db:5432/ferreteria_db

SECRET_KEY=PEGA_AQUI_EL_RESULTADO_DEL_COMANDO_ANTERIOR

POSTGRES_DB=ferreteria_db
POSTGRES_USER=ferreteria_user
POSTGRES_PASSWORD=ferreteria123

ALLOWED_ORIGINS=["http://localhost:5173"]
```

### 4. Levantar todo

```bash
make dev
```

Esto descarga las imágenes de Docker, instala dependencias, aplica las migraciones y levanta todo. La primera vez tarda 3-5 minutos.

### 5. Abrir el frontend

```
http://localhost:5173
```

El backend con Swagger (documentación de la API) está en:

```
http://localhost:8000/docs
```

---

## Comandos del día a día

```bash
# Levantar en background (sin ver logs)
make dev-d

# Ver logs en tiempo real
make logs

# Ver solo logs del backend
make logs-backend

# Detener todo
make down

# Abrir una terminal dentro del backend
make shell-backend

# Abrir psql (consola de PostgreSQL)
make shell-db
```

---

## Migraciones de base de datos

```bash
# Aplicar migraciones pendientes
make migrate

# Crear una nueva migración después de cambiar un modelo
make migration MSG="descripcion del cambio"

# Revertir la última migración
make migrate-down

# Ver historial de migraciones
make migrate-history
```

---

## Reiniciar desde cero (borra todos los datos)

```bash
make down-v
make dev
```

---

## Backup de la base de datos

```bash
make backup
```

El backup se guarda en `./backups/` con fecha y hora. Se mantienen los últimos 7 automáticamente.

---

## Estructura del proyecto

```
ferreteria-saas/
├── backend/          → FastAPI + Python
│   ├── app/
│   │   ├── api/      → endpoints HTTP
│   │   ├── models/   → tablas de base de datos
│   │   ├── schemas/  → validación de datos (Pydantic)
│   │   └── services/ → lógica de negocio (Excel, PDF, búsqueda)
│   └── alembic/      → migraciones de base de datos
├── frontend/         → React + TypeScript + Tailwind
│   └── src/
│       ├── api/      → llamadas al backend
│       ├── pages/    → pantallas de la app
│       ├── components/ → componentes reutilizables
│       └── hooks/    → lógica de estado
├── nginx/            → configuración del servidor (producción)
├── scripts/          → deploy.sh, backup.sh
├── docker-compose.yml       → entorno de desarrollo
├── docker-compose.prod.yml  → entorno de producción
└── Makefile          → todos los comandos
```

---

## Flujo principal de uso

1. **Registro** → crea tu cuenta con el nombre de tu ferretería
2. **Catálogos** → sube tu lista de precios en Excel (.xlsx)
3. **Mapeo** → indica qué columna es el nombre y cuál el precio
4. **Nueva cotización** → escribe el nombre del cliente
5. **Buscar productos** → escribe lo que buscas (tolera errores de escritura)
6. **Agregar** → click en + para agregar productos con cantidad
7. **PDF** → click en "Descargar PDF" → listo para enviar al cliente

---

## Variables de entorno — referencia completa

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL | `postgresql://user:pass@db:5432/dbname` |
| `SECRET_KEY` | Clave para firmar tokens JWT | string de 64 caracteres aleatorios |
| `POSTGRES_DB` | Nombre de la base de datos | `ferreteria_db` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `ferreteria_user` |
| `POSTGRES_PASSWORD` | Password de PostgreSQL | cualquier string seguro |
| `ALLOWED_ORIGINS` | Orígenes permitidos para CORS | `["http://localhost:5173"]` |
| `DEBUG` | Modo debug (activa Swagger) | `true` en dev, `false` en prod |

---

## Problemas comunes

**Docker no arranca:**
Asegúrate de que Docker Desktop esté abierto y corriendo.

**Error de puerto ocupado:**
Algún otro proceso usa el puerto 5432 o 8000. Detén PostgreSQL local si tienes uno instalado.

**El frontend no conecta con el backend:**
Verifica que `ALLOWED_ORIGINS` en `.env` incluya `http://localhost:5173`.

**Las migraciones fallan:**
```bash
make down-v
make dev
```

**Cambié un modelo Python y no se aplica:**
```bash
make migration MSG="describe el cambio"
make migrate
```
