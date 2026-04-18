"""
Configuración de Alembic para migraciones de base de datos.

Este archivo es el puente entre Alembic y tus modelos SQLAlchemy.

¿Cómo funciona Alembic?
  1. Lees tus modelos Python (las clases en app/models/)
  2. Lees el schema actual de la base de datos real
  3. Compara ambos y genera automáticamente el SQL de diferencias
  4. Guarda ese SQL como un archivo de migración numerado
  5. 'alembic upgrade head' aplica todas las migraciones pendientes

target_metadata = Base.metadata es la línea crítica:
  Le dice a Alembic "compara contra estos modelos".
  Sin esto, Alembic no sabe qué tablas existen en tu código.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Añadir el directorio backend al path para poder importar app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base  # noqa: E402 — debe ir después del sys.path
from app.core.config import settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Esta línea conecta Alembic con los modelos SQLAlchemy
target_metadata = Base.metadata

# Sobreescribir la URL de la DB con la del .env en lugar del alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Modo offline: genera SQL sin conectarse a la DB.
    Útil para revisar qué SQL se ejecutaría antes de aplicarlo.
    Comando: alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Modo online: se conecta a la DB y aplica las migraciones directamente.
    Es el modo normal — el que usas en deploy.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # sin pool en migraciones — conexión única
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # detectar cambios de tipo de columna
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
