"""Añadir campos de suscripción a organizations

Revision ID: 0002_subscription_fields
Revises: 0001_initial_schema
Create Date: 2025-01-01 00:00:01

Campos que se añaden:
  subscription_status — estado actual: trial / active / expired
  trial_ends_at       — cuándo vence el período de prueba (14 días desde registro)
  subscribed_at       — cuándo se activó la suscripción de pago (null si nunca)
  notes               — notas internas del admin (ej: "pagó por transferencia el 15 ene")

¿Por qué server_default en lugar de nullable sin default?
  La tabla organizations ya tiene datos (si corriste el sistema antes).
  Sin server_default, PostgreSQL no sabría qué valor poner en las filas
  existentes y el ALTER TABLE fallaría. Con server_default, PostgreSQL
  rellena las filas existentes con ese valor automáticamente.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_subscription_fields"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column(
        "subscription_status",
        sa.String(50),
        nullable=False,
        server_default="trial",
        comment="trial | active | expired",
    ))
    op.add_column("organizations", sa.Column(
        "trial_ends_at",
        sa.DateTime(timezone=True),
        nullable=True,
        comment="Fecha de vencimiento del período de prueba",
    ))
    op.add_column("organizations", sa.Column(
        "subscribed_at",
        sa.DateTime(timezone=True),
        nullable=True,
        comment="Cuándo se activó la suscripción de pago",
    ))
    op.add_column("organizations", sa.Column(
        "admin_notes",
        sa.Text(),
        nullable=True,
        comment="Notas internas del admin sobre esta organización",
    ))

    op.create_index(
        "ix_organizations_subscription_status",
        "organizations",
        ["subscription_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_organizations_subscription_status", "organizations")
    op.drop_column("organizations", "admin_notes")
    op.drop_column("organizations", "subscribed_at")
    op.drop_column("organizations", "trial_ends_at")
    op.drop_column("organizations", "subscription_status")
