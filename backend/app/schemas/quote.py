"""
Schemas de cotizaciones para la API.

Separación de schemas por operación:
  QuoteCreateRequest  → crear cotización vacía (solo datos del cliente)
  QuoteItemAddRequest → agregar un producto a la cotización
  QuoteItemUpdateRequest → cambiar cantidad o precio de un item
  QuoteResponse       → cotización completa con sus items
  QuoteListResponse   → cotización en lista (sin items, más ligero)

¿Por qué QuoteResponse incluye los items y QuoteListResponse no?
  En la pantalla de listado, solo necesitas mostrar:
    - número de cotización, cliente, fecha, total, estado
  Cargar los items de 50 cotizaciones para mostrar una lista sería
  N+1 queries innecesarias. QuoteListResponse es la versión ligera
  para listas, QuoteResponse es la versión completa para el detalle.
"""

import uuid
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, field_validator


# ── Requests ──────────────────────────────────────────────

class QuoteCreateRequest(BaseModel):
    """
    Datos para crear una cotización vacía.
    Los items se agregan después con POST /quotes/{id}/items.
    """
    client_name: str
    client_email: str | None = None
    client_phone: str | None = None
    notes: str | None = None

    @field_validator("client_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del cliente es obligatorio")
        return v.strip()


class QuoteItemAddRequest(BaseModel):
    """
    Agregar un producto a una cotización.

    product_id es opcional — el ferretero podría agregar un producto
    que no está en ningún catálogo (precio manual). En ese caso solo
    manda product_name y unit_price sin product_id.

    unit_price viene del frontend (el precio que mostró la búsqueda),
    pero el backend lo verifica contra el producto real si product_id existe.
    """
    product_id: uuid.UUID | None = None
    product_name: str
    product_code: str | None = None
    unit: str | None = None
    quantity: int = 1
    unit_price: Decimal
    discount_percentage: Decimal = Decimal("0.00")

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("La cantidad debe ser al menos 1")
        return v

    @field_validator("unit_price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return v

    @field_validator("discount_percentage")
    @classmethod
    def discount_valid(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 100:
            raise ValueError("El descuento debe estar entre 0 y 100")
        return v

    @field_validator("product_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del producto es obligatorio")
        return v.strip()


class QuoteItemUpdateRequest(BaseModel):
    """Actualizar cantidad o descuento de un item existente."""
    quantity: int | None = None
    unit_price: Decimal | None = None
    discount_percentage: Decimal | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("La cantidad debe ser al menos 1")
        return v


class QuoteUpdateRequest(BaseModel):
    """Actualizar datos generales de la cotización."""
    client_name: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    notes: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ("draft", "sent", "expired", "accepted"):
            raise ValueError("Estado inválido")
        return v


# ── Responses ─────────────────────────────────────────────

class QuoteItemResponse(BaseModel):
    """Una línea de producto dentro de la cotización."""
    id: uuid.UUID
    product_id: uuid.UUID | None
    product_name: str
    product_code: str | None
    unit: str | None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    discount_percentage: Decimal

    model_config = {"from_attributes": True}


class QuoteResponse(BaseModel):
    """Cotización completa con todos sus items. Para la vista de detalle."""
    id: uuid.UUID
    quote_number: str
    client_name: str
    client_email: str | None
    client_phone: str | None
    status: str
    notes: str | None
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[QuoteItemResponse]

    model_config = {"from_attributes": True}


class QuoteListItem(BaseModel):
    """Cotización resumida para listados. Sin items para mayor eficiencia."""
    id: uuid.UUID
    quote_number: str
    client_name: str
    status: str
    total_amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
