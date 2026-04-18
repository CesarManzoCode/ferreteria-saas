"""
Router de administración — gestión de organizaciones y suscripciones.

Todos los endpoints requieren role='admin'.
El admin puede:
  - Ver todas las organizaciones con sus métricas
  - Activar / desactivar / expirar suscripciones
  - Añadir notas internas
  - Ver estadísticas globales del sistema
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.catalog import Catalog
from app.models.organization import Organization
from app.models.quote import Quote
from app.models.user import User
from app.schemas.admin import (
    AdminStatsResponse,
    OrganizationAdminView,
    UpdateSubscriptionRequest,
)

router = APIRouter()


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency que verifica que el usuario es admin.
    Si no lo es, retorna 403 inmediatamente.
    Se usa igual que get_current_user pero con el check de rol extra.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user


def _build_org_view(org: Organization, db: Session) -> OrganizationAdminView:
    """Construye la vista de admin de una organización con sus métricas."""
    user_count    = db.query(User).filter(User.organization_id == org.id).count()
    catalog_count = db.query(Catalog).filter(Catalog.organization_id == org.id).count()
    quote_count   = db.query(Quote).filter(Quote.organization_id == org.id).count()

    return OrganizationAdminView(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        subscription_status=org.subscription_status,
        trial_ends_at=org.trial_ends_at,
        subscribed_at=org.subscribed_at,
        admin_notes=org.admin_notes,
        created_at=org.created_at,
        user_count=user_count,
        catalog_count=catalog_count,
        quote_count=quote_count,
    )


# ── GET /admin/stats ──────────────────────────────────────

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Estadísticas globales del sistema",
)
def get_stats(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AdminStatsResponse:
    """Dashboard de métricas globales para el admin."""
    orgs = db.query(Organization).all()

    # Calcular estados reales (tiene en cuenta trial vencido en memoria)
    trial_count   = sum(1 for o in orgs if o.subscription_status == "trial" and o.has_access)
    active_count  = sum(1 for o in orgs if o.subscription_status == "active")
    expired_count = sum(1 for o in orgs if not o.has_access)

    return AdminStatsResponse(
        total_organizations=len(orgs),
        trial_organizations=trial_count,
        active_organizations=active_count,
        expired_organizations=expired_count,
        total_users=db.query(User).count(),
        total_quotes=db.query(Quote).count(),
    )


# ── GET /admin/organizations ──────────────────────────────

@router.get(
    "/organizations",
    response_model=list[OrganizationAdminView],
    summary="Listar todas las organizaciones",
)
def list_organizations(
    status_filter: str | None = None,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[OrganizationAdminView]:
    """
    Lista todas las ferreterías registradas.
    Opcional: filtrar por subscription_status (trial/active/expired).
    """
    query = db.query(Organization).order_by(Organization.created_at.desc())
    if status_filter:
        query = query.filter(Organization.subscription_status == status_filter)

    orgs = query.all()
    return [_build_org_view(org, db) for org in orgs]


# ── GET /admin/organizations/{id} ─────────────────────────

@router.get(
    "/organizations/{org_id}",
    response_model=OrganizationAdminView,
    summary="Detalle de una organización",
)
def get_organization(
    org_id: uuid.UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> OrganizationAdminView:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return _build_org_view(org, db)


# ── PATCH /admin/organizations/{id}/subscription ──────────

@router.patch(
    "/organizations/{org_id}/subscription",
    response_model=OrganizationAdminView,
    summary="Activar / desactivar suscripción",
)
def update_subscription(
    org_id: uuid.UUID,
    request: UpdateSubscriptionRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> OrganizationAdminView:
    """
    Cambia el estado de suscripción de una organización.

    Para activar después de que el cliente pagó por transferencia:
      { "subscription_status": "active", "admin_notes": "Pagó $250 el 15 ene vía SPEI" }

    Para bloquear una cuenta:
      { "subscription_status": "expired" }
    """
    request.validate_status()

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    org.subscription_status = request.subscription_status

    # Si se activa → registrar fecha de activación
    if request.subscription_status == "active" and org.subscribed_at is None:
        org.subscribed_at = datetime.now(timezone.utc)

    if request.admin_notes is not None:
        org.admin_notes = request.admin_notes

    db.commit()
    db.refresh(org)
    return _build_org_view(org, db)


# ── PATCH /admin/organizations/{id}/toggle-active ────────

@router.patch(
    "/organizations/{org_id}/toggle-active",
    response_model=OrganizationAdminView,
    summary="Activar o desactivar cuenta (is_active)",
)
def toggle_active(
    org_id: uuid.UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> OrganizationAdminView:
    """Alterna is_active — bloquea/desbloquea sin cambiar la suscripción."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    org.is_active = not org.is_active
    db.commit()
    db.refresh(org)
    return _build_org_view(org, db)
