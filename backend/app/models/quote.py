"""
Modelos Quote y QuoteItem — el documento final del sistema.

Quote: la cotización en sí. Quién la pide, cuándo, en qué estado está.
QuoteItem: cada línea de producto dentro de la cotización.

La separación Quote/QuoteItem sigue el patrón clásico de
"header/líneas" que verás en cualquier sistema de ventas serio.
Una cotización puede tener 1 o 100 productos — la tabla Quote
siempre tiene 1 fila, QuoteItem tiene N filas.

Decisión crítica — por qué QuoteItem guarda el precio:
  Es tentador hacer que QuoteItem solo tenga product_id y quantity,
  y calcular el precio siempre desde el Product. NUNCA hagas eso.
  
  Si el ferretero actualiza su lista de precios mañana, ¿qué pasa
  con las cotizaciones de ayer? Deben mostrar el precio de ayer.
  Una cotización es un documento legal/comercial — el precio no
  puede cambiar retroactivamente.
  
  Por eso guardamos unit_price en QuoteItem: es una "fotografía"
  del precio en el momento de crear la cotización.

Estados de Quote:
  'draft'   → en construcción, no enviada al cliente
  'sent'    → enviada (PDF generado y descargado/enviado)
  'expired' → venció sin respuesta (futuro)
  'accepted'→ el cliente aceptó (futuro)
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Quote(Base, UUIDMixin, TimestampMixin):
    """
    Cotización generada para un cliente de la ferretería.
    
    client_name: el nombre que el ferretero escribe. No es un User
                 del sistema — es solo texto. El cliente final no
                 tiene cuenta en la plataforma.
    
    notes: campo libre para que el ferretero añada condiciones,
           tiempo de entrega, etc. Aparece al pie del PDF.
    
    quote_number: número legible por humanos. Los UUIDs son únicos
                  pero no son legibles. "COT-0042" es mejor para
                  mostrar al cliente que "a3f8c2d1-...".
    """
    __tablename__ = "quotes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # SET NULL: si se borra el user, la cotización sobrevive
        index=True,
    )

    quote_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Número legible: COT-0001, COT-0002, etc.",
    )
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Total calculado y guardado — no recalculado en cada consulta
    # Se actualiza cada vez que se añade/edita/borra un QuoteItem
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="quotes")
    items: Mapped[list["QuoteItem"]] = relationship(
        "QuoteItem",
        back_populates="quote",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Quote id={self.id} number={self.quote_number!r} status={self.status!r}>"


class QuoteItem(Base, UUIDMixin, TimestampMixin):
    """
    Una línea de producto dentro de una cotización.
    
    product_id es nullable intencionalmente:
      Si el catálogo se borra después de crear la cotización,
      el QuoteItem debe sobrevivir. Guardamos product_name como
      snapshot para que el PDF siempre muestre el nombre correcto.
    
    subtotal = quantity * unit_price
      Lo calculamos y guardamos para no recalcular en cada query.
      Es redundante pero correcto — la alternativa es calcular
      en Python cada vez y eso no escala bien en listas largas.
    """
    __tablename__ = "quote_items"

    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Snapshot del producto en el momento de crear el item
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Descuento opcional por línea (futuro — lo dejamos desde el inicio)
    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    quote: Mapped["Quote"] = relationship("Quote", back_populates="items")

    def __repr__(self) -> str:
        return f"<QuoteItem product={self.product_name!r} qty={self.quantity} price={self.unit_price}>"
