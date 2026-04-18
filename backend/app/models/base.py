"""
Modelo base compartido por todas las entidades del sistema.

Toda tabla del sistema hereda de esta clase. Esto garantiza que:
- Todas las tablas tienen un UUID como primary key (no integers predecibles)
- Todas tienen created_at y updated_at automáticos
- El patrón es consistente y no hay que repetir código

DeclarativeBase es el punto de entrada de SQLAlchemy moderno (v2.0+).
Todas las clases que hereden de Base serán reconocidas como tablas.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base de SQLAlchemy. Todas las tablas heredan de aquí."""
    pass


class TimestampMixin:
    """
    Mixin que añade created_at y updated_at a cualquier modelo.
    
    Un 'mixin' en Python es una clase que no se instancia sola — existe
    solo para añadir comportamiento a otras clases via herencia múltiple.
    
    server_default=func.now() → PostgreSQL pone el timestamp automáticamente
    onupdate=func.now() → PostgreSQL actualiza el timestamp en cada UPDATE
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """
    Mixin que añade un UUID como primary key.
    
    uuid.uuid4() genera un UUID aleatorio en Python antes de insertar.
    Esto es deliberado: preferimos generar el ID en la aplicación
    (no en la DB) para poder conocer el ID antes del INSERT si es necesario.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
