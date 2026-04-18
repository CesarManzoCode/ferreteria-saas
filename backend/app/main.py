"""
Punto de entrada de la aplicación FastAPI.

¿Qué hace este archivo?
  Define la instancia principal de FastAPI, configura CORS,
  y registra todos los routers (endpoints) de la API.

¿Qué es CORS?
  Cross-Origin Resource Sharing. Tu frontend corre en
  http://localhost:5173 (Vite) y tu backend en http://localhost:8000.
  Los navegadores bloquean por seguridad requests entre diferentes
  orígenes. CORS es la forma de decirle al browser
  "está bien, este origen tiene permiso".
  
  En producción, ALLOWED_ORIGINS solo incluirá tu dominio real.
  Nunca uses allow_origins=["*"] en producción — permitiría
  que cualquier sitio web haga requests a tu API con las
  credenciales del usuario.

Lifespan:
  FastAPI moderno usa un context manager 'lifespan' para código
  que corre al arrancar y al apagar. Es el reemplazo de los
  deprecated @app.on_event("startup").
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Código que corre al arrancar y apagar la aplicación.
    Todo antes del yield → startup.
    Todo después del yield → shutdown.
    """
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} arrancando...")
    yield
    # Shutdown
    print("👋 Aplicación cerrándose...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    # docs_url solo disponible cuando DEBUG=True
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middleware CORS ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,   # permite enviar cookies/tokens
    allow_methods=["*"],      # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],      # Authorization, Content-Type, etc.
)


# ── Health check ──────────────────────────────────────────
@app.get("/health", tags=["sistema"])
def health_check() -> dict:
    """
    Endpoint de salud. Usado por Docker y monitoring para verificar
    que el backend está vivo. Siempre debe retornar 200.
    """
    return {"status": "ok", "version": settings.APP_VERSION}


# ── Routers ───────────────────────────────────────────────
# Se irán registrando aquí conforme los construyamos.
# Ejemplo futuro:
#   from app.api.v1 import auth, catalogs, quotes
#   app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
