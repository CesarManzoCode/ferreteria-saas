"""
Modelo User — quien hace login en el sistema.

Decisión importante: User y Organization son entidades separadas.
Podría parecer excesivo para un MVP donde siempre hay 1 usuario por
ferretería, pero esta separación permite en el futuro:
  - Que el dueño invite a empleados
  - Que un empleado tenga permisos limitados
  - Que un mismo email pueda pertenecer a varias organizaciones

Cambiar esto después sería una migración muy costosa. Hacerlo bien
desde el inicio no añade complejidad visible — solo una tabla más.

Sobre el password:
  NUNCA se guarda el password en texto plano. Se guarda el hash
  generado por bcrypt. bcrypt es un algoritmo de hashing diseñado
  específicamente para passwords — es lento a propósito para dificultar
  ataques de fuerza bruta.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    Usuario del sistema. Siempre pertenece a una Organization.
    
    role: por ahora solo 'owner'. En el futuro: 'employee', 'viewer'.
          Guardarlo desde el inicio permite añadir permisos sin migrar.
    
    is_active: para suspender acceso sin borrar el usuario ni sus datos.
    """
    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="owner", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Referencia inversa — user.organization devuelve el objeto Organization completo
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
