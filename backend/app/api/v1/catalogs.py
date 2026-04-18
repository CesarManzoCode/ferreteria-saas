"""
Router de catálogos — endpoints para gestionar listas de precios.

Endpoints:
  POST   /catalogs/upload          → sube Excel, retorna columnas detectadas
  POST   /catalogs/process         → confirma mapeo, procesa y guarda productos
  GET    /catalogs                  → lista catálogos de la organización
  GET    /catalogs/{id}            → detalle de un catálogo
  DELETE /catalogs/{id}            → elimina catálogo y sus productos
  GET    /catalogs/{id}/search     → búsqueda fuzzy de productos

Sobre el flujo de dos pasos (upload → process):
  Podríamos hacer un solo endpoint que reciba el Excel + el mapeo.
  Pero entonces el frontend tendría que adivinar el mapeo sin mostrárselo
  al usuario. El flujo de dos pasos permite una mejor UX:
    Paso 1: frontend sube el Excel, backend retorna columnas detectadas
    Paso 2: frontend muestra checklist de mapeo, usuario confirma
    Paso 3: frontend manda confirmación, backend procesa

Sobre el guardado temporal del archivo:
  Entre el paso 1 y el paso 2, el archivo necesita seguir accesible.
  Lo guardamos en UPLOAD_DIR con un nombre único (UUID). El file_key
  que retorna el paso 1 es ese nombre de archivo — el frontend lo
  manda de vuelta en el paso 2.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.catalog import Catalog, Product
from app.models.user import User
from app.schemas.catalog import (
    CatalogProcessRequest,
    CatalogResponse,
    CatalogUploadResponse,
    SearchResponse,
)
from app.services.excel_service import parse_excel_file, process_catalog
from app.services.search_service import search_products

router = APIRouter()

# Extensiones de Excel permitidas
ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _get_upload_dir() -> Path:
    """Retorna el directorio de uploads, creándolo si no existe."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _verify_catalog_ownership(
    catalog_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session,
) -> Catalog:
    """
    Verifica que el catálogo existe y pertenece a la organización.
    Este es el check de multi-tenant: un usuario no puede ver ni
    modificar catálogos de otra organización.
    """
    catalog = (
        db.query(Catalog)
        .filter(Catalog.id == catalog_id, Catalog.organization_id == organization_id)
        .first()
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catálogo no encontrado",
        )
    return catalog


# ── POST /upload ──────────────────────────────────────────

@router.post(
    "/upload",
    response_model=CatalogUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Subir archivo Excel (paso 1 de 2)",
)
async def upload_excel(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
) -> CatalogUploadResponse:
    """
    Recibe el Excel, lo guarda temporalmente y retorna las columnas detectadas.
    
    UploadFile de FastAPI maneja automáticamente el multipart/form-data.
    El archivo se guarda con un UUID como nombre para evitar colisiones
    entre usuarios que suban archivos simultáneamente.
    """
    # Validar extensión
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido. Solo se aceptan: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo supera el máximo de {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    # Guardar temporalmente con nombre único
    file_key = f"{uuid.uuid4()}{extension}"
    file_path = _get_upload_dir() / file_key

    file_path.write_bytes(content)

    # Parsear estructura del Excel
    try:
        parse_result = parse_excel_file(file_path)
    except ValueError as e:
        file_path.unlink(missing_ok=True)  # limpiar si falla
        raise HTTPException(status_code=400, detail=str(e)) from e

    return CatalogUploadResponse(
        file_key=file_key,
        detected_columns=parse_result["detected_columns"],
        suggested_mapping=parse_result["suggested_mapping"],
        row_count=parse_result["row_count"],
    )


# ── POST /process ─────────────────────────────────────────

@router.post(
    "/process",
    response_model=CatalogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Procesar Excel con mapeo confirmado (paso 2 de 2)",
)
def process_catalog_endpoint(
    request: CatalogProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogResponse:
    """
    Toma el file_key del paso 1 y el mapeo confirmado, procesa el Excel
    y guarda todos los productos en la base de datos.
    
    Usa inserción bulk (INSERT de muchas filas en un solo query) en lugar
    de insertar producto por producto. Para 3,000 productos:
      - Inserción por producto: ~3,000 queries → lento
      - Inserción bulk: 1 query → rápido (< 1 segundo)
    """
    # Verificar que el archivo temporal existe
    file_path = _get_upload_dir() / request.file_key
    if not file_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Archivo no encontrado. Por favor sube el Excel nuevamente.",
        )

    # Crear el catálogo primero (necesitamos su ID para los productos)
    catalog = Catalog(
        organization_id=current_user.organization_id,
        name=request.catalog_name,
        source_type=request.source_type,
        distributor_name=request.distributor_name,
        margin_percentage=request.margin_percentage,
        original_filename=request.file_key,
    )
    db.add(catalog)
    db.flush()  # obtenemos catalog.id sin hacer commit aún

    # Procesar Excel con pandas
    try:
        column_mapping_dict = request.column_mapping.model_dump()
        products_data, skipped = process_catalog(
            file_path=file_path,
            column_mapping=column_mapping_dict,
            organization_id=current_user.organization_id,
            catalog_id=catalog.id,
            margin_percentage=request.margin_percentage,
        )
    except Exception as e:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error procesando el archivo: {str(e)}",
        ) from e

    if not products_data:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="No se encontraron productos válidos en el archivo.",
        )

    # Inserción bulk — un solo INSERT con todos los productos
    # db.bulk_insert_mappings es más eficiente que db.add() en loop
    db.bulk_insert_mappings(Product, products_data)

    # Actualizar contador en el catálogo
    catalog.row_count = len(products_data)
    db.commit()
    db.refresh(catalog)

    # Limpiar archivo temporal
    file_path.unlink(missing_ok=True)

    return CatalogResponse.model_validate(catalog)


# ── GET / ─────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[CatalogResponse],
    summary="Listar catálogos de la organización",
)
def list_catalogs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CatalogResponse]:
    """Retorna todos los catálogos de la organización del usuario."""
    catalogs = (
        db.query(Catalog)
        .filter(Catalog.organization_id == current_user.organization_id)
        .order_by(Catalog.created_at.desc())
        .all()
    )
    return [CatalogResponse.model_validate(c) for c in catalogs]


# ── GET /{id} ─────────────────────────────────────────────

@router.get(
    "/{catalog_id}",
    response_model=CatalogResponse,
    summary="Detalle de un catálogo",
)
def get_catalog(
    catalog_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CatalogResponse:
    catalog = _verify_catalog_ownership(catalog_id, current_user.organization_id, db)
    return CatalogResponse.model_validate(catalog)


# ── DELETE /{id} ──────────────────────────────────────────

@router.delete(
    "/{catalog_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar catálogo y sus productos",
)
def delete_catalog(
    catalog_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    catalog = _verify_catalog_ownership(catalog_id, current_user.organization_id, db)
    db.delete(catalog)  # cascade borrará los productos automáticamente
    db.commit()


# ── GET /{id}/search ──────────────────────────────────────

@router.get(
    "/{catalog_id}/search",
    response_model=SearchResponse,
    summary="Buscar productos en un catálogo (fuzzy search)",
)
def search_in_catalog(
    catalog_id: uuid.UUID,
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """
    Búsqueda fuzzy de productos dentro de un catálogo específico.
    
    Args:
        q: texto de búsqueda (ej: "tornillo 3/4", "valvula esfera")
        limit: máximo de resultados (default 20, máximo 50)
    """
    _verify_catalog_ownership(catalog_id, current_user.organization_id, db)

    limit = min(limit, 50)  # cap de seguridad

    return search_products(
        db=db,
        organization_id=current_user.organization_id,
        query=q,
        catalog_id=catalog_id,
        limit=limit,
    )


@router.get(
    "/search/all",
    response_model=SearchResponse,
    summary="Buscar en todos los catálogos de la organización",
)
def search_all_catalogs(
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Búsqueda fuzzy sobre todos los catálogos de la organización."""
    limit = min(limit, 50)
    return search_products(
        db=db,
        organization_id=current_user.organization_id,
        query=q,
        catalog_id=None,
        limit=limit,
    )
