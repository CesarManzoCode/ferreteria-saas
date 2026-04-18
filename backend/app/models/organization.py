"""
Modelo Organization — la raíz del sistema multi-tenant.

En un SaaS multi-tenant, 'tenant' es el cliente que paga (la ferretería).
Organization es esa ferretería. Todo dato de negocio en el sistema
tiene una referencia a organization_id — eso es lo que separa los datos
de una ferretería de otra.

Relaciones:
    Organization 1 → N Users      (empleados de la ferretería)
    Organization 1 → N Catalogs   (sus listas de precios)
    Organization 1 → N Quotes     (sus cotizaciones)
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    """
    Representa una ferretería (el tenant).
    
    slug: identificador URL-friendly único. Ejemplo: si la ferretería
          se llama "Ferretería García", su slug sería "ferreteria-garcia".
          Útil para URLs limpias y como identificador legible.
    
    is_active: permite desactivar una cuenta sin borrarla.
               Borrar datos en producción casi nunca es la respuesta correcta.
    """
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships — SQLAlchemy carga estos objetos relacionados cuando los necesitas
    # 'back_populates' crea la referencia inversa: user.organization funciona automáticamente
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    catalogs: Mapped[list["Catalog"]] = relationship("Catalog", back_populates="organization")
    quotes: Mapped[list["Quote"]] = relationship("Quote", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name!r}>"
