"""
Modelo Organization — la raíz del sistema multi-tenant.

Relaciones:
    Organization 1 → N Users
    Organization 1 → N Catalogs
    Organization 1 → N Quotes

Suscripción:
    subscription_status: 'trial' | 'active' | 'expired'
    trial_ends_at: fecha de vencimiento del trial (now + 14 días al crear)
    subscribed_at: cuándo el admin activó la cuenta de pago
    admin_notes:   notas internas del admin
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

TRIAL_DAYS = 14


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    subscription_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="trial", index=True,
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    subscribed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    catalogs: Mapped[list["Catalog"]] = relationship("Catalog", back_populates="organization")
    quotes: Mapped[list["Quote"]] = relationship("Quote", back_populates="organization")

    def set_trial(self) -> None:
        """Inicializa el trial al crear la organización."""
        self.subscription_status = "trial"
        self.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)

    @property
    def is_trial_expired(self) -> bool:
        if self.subscription_status != "trial":
            return False
        if self.trial_ends_at is None:
            return False
        return datetime.now(timezone.utc) > self.trial_ends_at

    @property
    def has_access(self) -> bool:
        if self.subscription_status == "active":
            return True
        if self.subscription_status == "trial":
            return not self.is_trial_expired
        return False

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name!r} status={self.subscription_status!r}>"
