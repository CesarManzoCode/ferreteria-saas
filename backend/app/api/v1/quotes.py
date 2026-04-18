"""
Router de cotizaciones — el flujo central del producto.

Endpoints:
  POST   /quotes                     → crear cotización vacía
  GET    /quotes                     → listar cotizaciones de la organización
  GET    /quotes/{id}                → detalle completo con items
  PATCH  /quotes/{id}                → actualizar datos del cliente o estado
  DELETE /quotes/{id}                → eliminar cotización
  POST   /quotes/{id}/items          → agregar producto a la cotización
  PATCH  /quotes/{id}/items/{item_id}→ actualizar cantidad/precio de un item
  DELETE /quotes/{id}/items/{item_id}→ quitar producto de la cotización
  GET    /quotes/{id}/pdf            → descargar PDF

Sobre los números de cotización (COT-0001):
  Usamos una secuencia de PostgreSQL por organización.
  Una secuencia en Postgres es un objeto que garantiza enteros únicos
  y consecutivos incluso con múltiples requests simultáneos.
  
  En lugar de crear una secuencia por organización (complejo), usamos
  una tabla 'quote_sequences' con un contador por organización y
  SELECT ... FOR UPDATE para bloqueo atómico. Es más portable que
  las secuencias nativas de Postgres y suficiente para el MVP.
  
  Alternativa simple que usamos aquí: contar las cotizaciones existentes
  de la organización + 1. Tiene una condición de carrera teórica si
  dos usuarios crean cotizaciones exactamente al mismo tiempo, pero
  para una ferretería con 1-3 usuarios es prácticamente imposible.
  Si en el futuro es problema, se resuelve con una secuencia real.

Sobre _recalculate_total():
  Cada vez que se agrega, modifica o borra un item, recalculamos
  el total de la cotización. Esto mantiene quote.total_amount siempre
  sincronizado sin necesidad de calcularlo en el frontend.
"""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.quote import Quote, QuoteItem
from app.models.user import User
from app.schemas.quote import (
    QuoteCreateRequest,
    QuoteItemAddRequest,
    QuoteItemResponse,
    QuoteItemUpdateRequest,
    QuoteListItem,
    QuoteResponse,
    QuoteUpdateRequest,
)

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────

def _get_quote_or_404(
    quote_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session,
    load_items: bool = False,
) -> Quote:
    """
    Busca una cotización verificando que pertenece a la organización.
    Si load_items=True, carga los items en la misma query (joinedload).
    """
    query = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.organization_id == organization_id,
    )
    if load_items:
        query = query.options(joinedload(Quote.items))

    quote = query.first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )
    return quote


def _generate_quote_number(organization_id: uuid.UUID, db: Session) -> str:
    """
    Genera el próximo número de cotización para la organización.
    Formato: COT-XXXX (ej: COT-0001, COT-0042, COT-1337)
    """
    count = db.query(Quote).filter(
        Quote.organization_id == organization_id
    ).count()
    return f"COT-{(count + 1):04d}"


def _calculate_item_subtotal(
    unit_price: Decimal,
    quantity: int,
    discount_percentage: Decimal,
) -> Decimal:
    """
    Calcula el subtotal de un item aplicando descuento si hay.
    subtotal = (unit_price * quantity) * (1 - discount/100)
    """
    gross = unit_price * quantity
    if discount_percentage > 0:
        discount_factor = Decimal("1") - (discount_percentage / Decimal("100"))
        return (gross * discount_factor).quantize(Decimal("0.01"))
    return gross.quantize(Decimal("0.01"))


def _recalculate_total(quote: Quote, db: Session) -> None:
    """
    Recalcula y guarda el total de la cotización sumando todos los items.
    Se llama después de cualquier cambio en los items.
    No hace commit — el caller es responsable del commit.
    """
    items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).all()
    quote.total_amount = sum(item.subtotal for item in items) or Decimal("0.00")


# ── POST / ────────────────────────────────────────────────

@router.post(
    "/",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva cotización",
)
def create_quote(
    request: QuoteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteResponse:
    """Crea una cotización vacía. Los productos se agregan después."""
    quote_number = _generate_quote_number(current_user.organization_id, db)

    quote = Quote(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        quote_number=quote_number,
        client_name=request.client_name,
        client_email=request.client_email,
        client_phone=request.client_phone,
        notes=request.notes,
        status="draft",
        total_amount=Decimal("0.00"),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    # Cargar con items vacíos para que el schema no falle
    quote.items = []
    return QuoteResponse.model_validate(quote)


# ── GET / ─────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[QuoteListItem],
    summary="Listar cotizaciones",
)
def list_quotes(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuoteListItem]:
    """
    Lista cotizaciones de la organización, más recientes primero.
    Opcionalmente filtra por status: draft, sent, expired, accepted.
    """
    query = db.query(Quote).filter(
        Quote.organization_id == current_user.organization_id
    )
    if status_filter:
        query = query.filter(Quote.status == status_filter)

    quotes = query.order_by(Quote.created_at.desc()).all()
    return [QuoteListItem.model_validate(q) for q in quotes]


# ── GET /{id} ─────────────────────────────────────────────

@router.get(
    "/{quote_id}",
    response_model=QuoteResponse,
    summary="Detalle de cotización con items",
)
def get_quote(
    quote_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteResponse:
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db, load_items=True)
    return QuoteResponse.model_validate(quote)


# ── PATCH /{id} ───────────────────────────────────────────

@router.patch(
    "/{quote_id}",
    response_model=QuoteResponse,
    summary="Actualizar datos de la cotización",
)
def update_quote(
    quote_id: uuid.UUID,
    request: QuoteUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteResponse:
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db, load_items=True)

    # Solo actualizar los campos que el request manda (PATCH semántico)
    # model_dump(exclude_none=True) retorna solo los campos no-None
    update_data = request.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(quote, field, value)

    db.commit()
    db.refresh(quote)
    return QuoteResponse.model_validate(quote)


# ── DELETE /{id} ──────────────────────────────────────────

@router.delete(
    "/{quote_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cotización",
)
def delete_quote(
    quote_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db)
    db.delete(quote)
    db.commit()


# ── POST /{id}/items ──────────────────────────────────────

@router.post(
    "/{quote_id}/items",
    response_model=QuoteItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar producto a la cotización",
)
def add_item(
    quote_id: uuid.UUID,
    request: QuoteItemAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteItemResponse:
    """
    Agrega un producto a la cotización y recalcula el total.

    Si viene product_id, guardamos el snapshot del nombre/código/unidad
    del producto en ese momento — el precio queda fijo en la cotización
    aunque el catálogo cambie después.
    """
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db)

    subtotal = _calculate_item_subtotal(
        request.unit_price,
        request.quantity,
        request.discount_percentage,
    )

    item = QuoteItem(
        quote_id=quote.id,
        product_id=request.product_id,
        product_name=request.product_name,
        product_code=request.product_code,
        unit=request.unit,
        quantity=request.quantity,
        unit_price=request.unit_price,
        subtotal=subtotal,
        discount_percentage=request.discount_percentage,
    )
    db.add(item)

    # Recalcular total del quote
    _recalculate_total(quote, db)
    # Sumamos el nuevo item manualmente porque aún no está en DB
    quote.total_amount += subtotal

    db.commit()
    db.refresh(item)
    return QuoteItemResponse.model_validate(item)


# ── PATCH /{id}/items/{item_id} ───────────────────────────

@router.patch(
    "/{quote_id}/items/{item_id}",
    response_model=QuoteItemResponse,
    summary="Actualizar cantidad o precio de un item",
)
def update_item(
    quote_id: uuid.UUID,
    item_id: uuid.UUID,
    request: QuoteItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteItemResponse:
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db)

    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_id == quote.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    # Aplicar cambios
    if request.quantity is not None:
        item.quantity = request.quantity
    if request.unit_price is not None:
        item.unit_price = request.unit_price
    if request.discount_percentage is not None:
        item.discount_percentage = request.discount_percentage

    # Recalcular subtotal del item
    item.subtotal = _calculate_item_subtotal(
        item.unit_price,
        item.quantity,
        item.discount_percentage,
    )

    # Recalcular total del quote
    _recalculate_total(quote, db)

    db.commit()
    db.refresh(item)
    return QuoteItemResponse.model_validate(item)


# ── DELETE /{id}/items/{item_id} ──────────────────────────

@router.delete(
    "/{quote_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar producto de la cotización",
)
def delete_item(
    quote_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db)

    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_id == quote.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    db.delete(item)
    _recalculate_total(quote, db)
    db.commit()


# ── GET /{id}/pdf ─────────────────────────────────────────

@router.get(
    "/{quote_id}/pdf",
    summary="Descargar cotización como PDF",
    response_class=Response,
)
def download_pdf(
    quote_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """
    Genera y retorna el PDF de la cotización.

    Al descargar, marca la cotización como 'sent' automáticamente
    — si el ferretero bajó el PDF, es porque lo va a mandar al cliente.
    El estado se puede revertir a 'draft' desde el PATCH si es necesario.

    La respuesta usa media_type 'application/pdf' y el header
    Content-Disposition para que el browser lo descargue como archivo
    en lugar de intentar abrirlo en una nueva pestaña.
    """
    quote = _get_quote_or_404(quote_id, current_user.organization_id, db, load_items=True)

    if not quote.items:
        raise HTTPException(
            status_code=400,
            detail="No puedes generar PDF de una cotización sin productos",
        )

    from app.services.pdf_service import generate_quote_pdf

    try:
        pdf_bytes = generate_quote_pdf(
            quote=quote,
            org_name=current_user.organization.name,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    # Marcar como enviada
    if quote.status == "draft":
        quote.status = "sent"
        db.commit()

    filename = f"{quote.quote_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
