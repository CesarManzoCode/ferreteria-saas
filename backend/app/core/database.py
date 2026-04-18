"""
Configuración de la conexión a PostgreSQL y gestión de sesiones.

¿Qué es una sesión en SQLAlchemy?
  Una sesión es una "unidad de trabajo". Agrupa todas las operaciones
  de base de datos (SELECTs, INSERTs, UPDATEs) en una transacción.
  Al hacer session.commit(), todo se guarda. Al hacer session.rollback(),
  todo se cancela. Si algo explota en medio, rollback automático.

¿Qué es un engine?
  Es la conexión física a la base de datos. Solo hay uno por aplicación.
  El engine maneja un pool de conexiones — en lugar de abrir y cerrar
  una conexión por cada request HTTP (caro), mantiene varias abiertas
  y las presta. Cuando el request termina, la conexión vuelve al pool.

¿Qué es get_db()?
  Es un "dependency" de FastAPI. Cuando un endpoint lo declara como
  parámetro, FastAPI automáticamente:
    1. Crea una sesión antes del request
    2. La inyecta en el endpoint
    3. La cierra al terminar (aunque haya error)
  
  El patrón 'yield' con try/finally garantiza que la sesión SIEMPRE
  se cierra, incluso si el endpoint lanza una excepción.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# El engine es la conexión al pool de PostgreSQL
# pool_pre_ping=True: verifica que la conexión esté viva antes de usarla
# Evita errores cuando PostgreSQL cierra conexiones idle después de un tiempo
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,        # conexiones mantenidas abiertas permanentemente
    max_overflow=10,    # conexiones extra permitidas en picos de carga
)

# SessionLocal es una fábrica — cada llamada crea una nueva sesión independiente
SessionLocal = sessionmaker(
    autocommit=False,   # NUNCA autocommit — siempre explícito
    autoflush=False,    # no enviar SQL automáticamente, esperar al commit
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency de FastAPI para inyectar una sesión de base de datos.
    
    Uso en un endpoint:
        @router.get("/products")
        def list_products(db: Session = Depends(get_db)):
            return db.query(Product).all()
    
    FastAPI llama a esta función, ejecuta hasta el 'yield' (entrega la sesión),
    corre el endpoint, y luego continúa después del yield para hacer cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
