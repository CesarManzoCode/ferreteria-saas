"""
Schemas de catálogos y productos para la API.

Separación de responsabilidades entre schemas:
  CatalogCreate      → qué manda el frontend al crear un catálogo
  ColumnMapping      → cómo el ferretero mapea sus columnas de Excel
  CatalogResponse    → qué retorna la API sobre un catálogo
  ProductResponse    → qué retorna la API sobre un producto
  SearchResponse     → resultado de búsqueda fuzzy (incluye el score)

¿Por qué ColumnMapping es un schema separado?
  El proceso de subir un catálogo tiene dos pasos:
    1. POST /catalogs/upload   → sube el Excel, retorna las columnas detectadas
    2. POST /catalogs/process  → el ferretero confirma el mapeo, se procesan los productos
  
  Esto permite que el frontend muestre una UI de confirmación antes
  de procesar — el ferretero ve "detecté estas columnas, ¿es correcto?"
  y puede corregir antes de que se guarden 3,000 productos con columnas
  equivocadas.
"""

import uuid
from decimal import Decimal

from pydantic import BaseModel, field_validator


# ── Upload y mapeo ────────────────────────────────────────

class ColumnMapping(BaseModel):
    """
    Mapeo de columnas del Excel del ferretero a los campos del sistema.
    
    Solo name_column y price_column son obligatorios — los demás son
    opcionales porque no todos los Excel los tienen.
    
    Ejemplo de lo que manda el frontend:
    {
        "name_column": "DESCRIPCION",
        "price_column": "PRECIO UNITARIO",
        "price_with_tax_column": "PRECIO C/IVA",
        "product_code_column": "CLAVE",
        "category_column": null,
        "unit_column": "UNIDAD"
    }
    """
    name_column: str
    price_column: str
    price_with_tax_column: str | None = None
    product_code_column: str | None = None
    category_column: str | None = None
    unit_column: str | None = None
    brand_column: str | None = None
    description_column: str | None = None

    @field_validator("name_column", "price_column")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo es obligatorio")
        return v.strip()


class CatalogUploadResponse(BaseModel):
    """
    Respuesta al subir el Excel antes de procesarlo.
    
    file_key: identificador temporal del archivo guardado en disco.
              El frontend lo manda de vuelta en el paso de confirmación.
    detected_columns: todas las columnas que pandas encontró en el Excel.
                      El frontend las muestra para que el ferretero mapee.
    suggested_mapping: el sistema intenta adivinar qué columna es qué
                       usando fuzzy matching sobre los nombres de columna.
                       El ferretero solo confirma o corrige.
    row_count: cuántas filas tiene el Excel (para mostrar "3,421 productos")
    """
    file_key: str
    detected_columns: list[str]
    suggested_mapping: dict[str, str | None]
    row_count: int


class CatalogProcessRequest(BaseModel):
    """
    Request para confirmar el mapeo y procesar el Excel.
    Combina el file_key del paso anterior con el mapeo confirmado.
    """
    file_key: str
    catalog_name: str
    column_mapping: ColumnMapping
    source_type: str = "own"
    distributor_name: str | None = None
    margin_percentage: Decimal | None = None

    @field_validator("catalog_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del catálogo es obligatorio")
        return v.strip()

    @field_validator("source_type")
    @classmethod
    def valid_source_type(cls, v: str) -> str:
        if v not in ("own", "distributor"):
            raise ValueError("source_type debe ser 'own' o 'distributor'")
        return v


# ── Responses ─────────────────────────────────────────────

class CatalogResponse(BaseModel):
    """Datos de un catálogo que retorna la API."""
    id: uuid.UUID
    name: str
    source_type: str
    distributor_name: str | None
    margin_percentage: Decimal | None
    original_filename: str | None
    row_count: int

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    """Datos de un producto que retorna la API."""
    id: uuid.UUID
    name: str
    base_price: Decimal
    price_with_tax: Decimal | None
    product_code: str | None
    category: str | None
    unit: str | None
    brand: str | None

    model_config = {"from_attributes": True}


class ProductSearchResult(BaseModel):
    """
    Resultado de búsqueda fuzzy — incluye el producto y su score de similitud.
    
    score: número de 0 a 100. 100 = coincidencia perfecta.
           El frontend puede mostrarlo visualmente o usarlo para
           ordenar los resultados (ya vienen ordenados por score desc).
    """
    product: ProductResponse
    score: float


class SearchResponse(BaseModel):
    """Respuesta completa de una búsqueda."""
    query: str
    results: list[ProductSearchResult]
    total: int
