"""
Schemas y dependency para el panel de administración.

El admin es un usuario con role='admin' — no es una entidad separada,
es el mismo User con un rol diferente. Esto simplifica mucho el sistema:
  - No hay tabla separada de admins
  - El admin puede ver la UI normal también
  - Para hacer admin a alguien: UPDATE users SET role='admin' WHERE email='...'
    (o desde el Makefile: make create-admin EMAIL=...)

OrganizationAdminView incluye campos que los usuarios normales no ven:
  - subscription_status, trial_ends_at, subscribed_at
  - admin_notes
  - total de usuarios, catálogos y cotizaciones
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrganizationAdminView(BaseModel):
    """Vista completa de una organización para el panel de admin."""
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    subscription_status: str
    trial_ends_at: datetime | None
    subscribed_at: datetime | None
    admin_notes: str | None
    created_at: datetime
    # Métricas
    user_count: int = 0
    catalog_count: int = 0
    quote_count: int = 0

    model_config = {"from_attributes": True}


class UpdateSubscriptionRequest(BaseModel):
    """Request para cambiar el estado de suscripción de una organización."""
    subscription_status: str  # 'trial' | 'active' | 'expired'
    admin_notes: str | None = None

    def validate_status(self) -> None:
        valid = {"trial", "active", "expired"}
        if self.subscription_status not in valid:
            raise ValueError(f"status debe ser uno de: {valid}")


class AdminStatsResponse(BaseModel):
    """Estadísticas globales del sistema para el dashboard de admin."""
    total_organizations: int
    trial_organizations: int
    active_organizations: int
    expired_organizations: int
    total_users: int
    total_quotes: int
