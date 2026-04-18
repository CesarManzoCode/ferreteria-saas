"""
Punto de entrada del módulo models.

Importar desde aquí en lugar de desde cada archivo individual:
  ✓ from app.models import User, Organization, Product
  ✗ from app.models.user import User  (funciona pero rompe encapsulación)

El orden de los imports importa: Base debe importarse antes que
cualquier modelo que la use. Los modelos con ForeignKeys deben
importarse después de los modelos que referencian.
"""

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.organization import Organization
from app.models.user import User
from app.models.catalog import Catalog, Product
from app.models.quote import Quote, QuoteItem

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "Organization",
    "User",
    "Catalog",
    "Product",
    "Quote",
    "QuoteItem",
]
