"""
Servicio de procesamiento de archivos Excel.

¿Qué es la capa de 'services'?
  En una arquitectura limpia, los 'services' contienen la lógica de negocio
  pura — lo que el sistema HACE, separado de cómo se comunica (API)
  y cómo persiste datos (repositorio/DB).

  Esta separación permite:
    - Testear la lógica sin levantar un servidor HTTP
    - Reutilizar la lógica desde distintos endpoints
    - Cambiar pandas por otra librería sin tocar los endpoints

  El endpoint llama al service, el service hace el trabajo, retorna datos.
  El endpoint no sabe nada de pandas. El service no sabe nada de HTTP.

Flujo de este servicio:
  [1] parse_excel_file()   → lee el archivo, retorna columnas detectadas + sugerencias
  [2] process_catalog()    → aplica el mapeo, transforma y valida cada fila
                             retorna lista de dicts listos para insertar en DB
"""

import unicodedata
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from rapidfuzz import process as fuzz_process

# Columnas "canónicas" que el sistema conoce
# Se usan para auto-detectar qué columna del Excel es qué
CANONICAL_COLUMNS = {
    "name_column": [
        "nombre", "descripcion", "descripción", "producto", "articulo",
        "artículo", "item", "detalle", "concepto", "material",
    ],
    "price_column": [
        "precio", "precio unitario", "precio_unitario", "p.u.", "pu",
        "costo", "valor", "importe", "precio sin iva", "precio_sin_iva",
    ],
    "price_with_tax_column": [
        "precio con iva", "precio_con_iva", "precio iva", "precio+iva",
        "precio final", "total", "precio al publico",
    ],
    "product_code_column": [
        "clave", "codigo", "código", "sku", "referencia", "ref",
        "id", "num", "número", "numero",
    ],
    "category_column": [
        "categoria", "categoría", "departamento", "familia", "tipo",
        "grupo", "linea", "línea",
    ],
    "unit_column": [
        "unidad", "um", "u.m.", "medida", "presentacion", "presentación",
    ],
    "brand_column": [
        "marca", "fabricante", "proveedor",
    ],
}


def normalize_string(text: str) -> str:
    """
    Normaliza un string para búsqueda fuzzy.
    
    Transforma: "Tornillo Autorroscante (PH) #6 x 3/4"
    En:         "tornillo autorroscante ph 6 x 3 4"
    
    ¿Por qué quitar acentos y caracteres especiales?
      RapidFuzz compara carácter por carácter. Si el usuario busca
      "valvula" y el producto se llama "válvula", sin normalización
      el score baja porque 'a' ≠ 'á'. Normalizando ambos, la comparación
      es más precisa.
    
    unicodedata.normalize('NFKD', ...) descompone caracteres Unicode:
      'á' → 'a' + acento_separado
    encode('ascii', 'ignore') descarta los acentos separados.
    """
    if not isinstance(text, str):
        text = str(text)
    # Lowercase
    text = text.lower()
    # Quitar acentos: NFKD separa carácter + diacrítico, luego filtramos diacríticos
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Reemplazar caracteres no alfanuméricos con espacios
    text = "".join(c if c.isalnum() else " " for c in text)
    # Colapsar espacios múltiples
    text = " ".join(text.split())
    return text


def suggest_column_mapping(excel_columns: list[str]) -> dict[str, str | None]:
    """
    Intenta adivinar qué columna del Excel corresponde a cada campo.

    Usa RapidFuzz para comparar los nombres de columna del Excel contra
    los nombres canónicos conocidos. Si la similitud supera el threshold,
    sugiere ese mapeo.

    Ejemplo:
      Excel tiene columnas: ["CLAVE", "DESCRIPCION DEL PRODUCTO", "PRECIO C/IVA"]
      Resultado: {
        "name_column": "DESCRIPCION DEL PRODUCTO",    (score 89)
        "price_column": None,                          (nada supera threshold)
        "price_with_tax_column": "PRECIO C/IVA",      (score 82)
        "product_code_column": "CLAVE",               (score 95)
        ...
      }
    """
    # Normalizar columnas del Excel para comparación
    normalized_excel = {col: normalize_string(col) for col in excel_columns}

    suggestions: dict[str, str | None] = {}
    used_columns: set[str] = set()  # evita asignar la misma columna dos veces

    for field, candidates in CANONICAL_COLUMNS.items():
        best_match: str | None = None
        best_score: float = 0.0

        for excel_col, normalized_col in normalized_excel.items():
            if excel_col in used_columns:
                continue
            # Comparar contra todos los candidatos canónicos
            result = fuzz_process.extractOne(normalized_col, candidates, score_cutoff=55)
            if result and result[1] > best_score:
                best_score = result[1]
                best_match = excel_col

        if best_match:
            suggestions[field] = best_match
            used_columns.add(best_match)
        else:
            suggestions[field] = None

    return suggestions


def parse_excel_file(file_path: Path) -> dict:
    """
    Lee el Excel y retorna columnas detectadas + sugerencias de mapeo.
    No procesa los datos aún — solo inspecciona la estructura.

    Returns:
        {
            "detected_columns": ["CLAVE", "DESCRIPCION", "PRECIO"],
            "suggested_mapping": {"name_column": "DESCRIPCION", ...},
            "row_count": 3421,
        }
    
    Soporta .xlsx y .xls. Pandas maneja ambos automáticamente.
    header=0 → la primera fila es el encabezado (nombres de columna).
    """
    try:
        # engine=None → pandas detecta automáticamente xlsx vs xls
        df = pd.read_excel(file_path, header=0, engine=None)
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo Excel: {e}") from e

    # Limpiar nombres de columna: quitar espacios al inicio/fin, convertir a string
    df.columns = [str(col).strip() for col in df.columns]

    # Eliminar filas completamente vacías
    df = df.dropna(how="all")

    detected_columns = list(df.columns)
    row_count = len(df)

    if row_count == 0:
        raise ValueError("El archivo Excel está vacío o no tiene filas de datos")

    if len(detected_columns) < 2:
        raise ValueError("El archivo debe tener al menos 2 columnas (nombre y precio)")

    suggested_mapping = suggest_column_mapping(detected_columns)

    return {
        "detected_columns": detected_columns,
        "suggested_mapping": suggested_mapping,
        "row_count": row_count,
    }


def _parse_price(value) -> Decimal | None:
    """
    Convierte un valor de celda Excel a Decimal de forma segura.

    Los precios en Excel pueden venir como:
      - float: 45.5
      - string: "$45.50", "45,50", "45.50 MXN"
      - NaN: celda vacía
    
    Retorna None si no se puede parsear (el registro se omitirá si
    es el precio principal, o se ignorará si es opcional).
    """
    if pd.isna(value):
        return None
    # Si es número, convertir directamente
    if isinstance(value, (int, float)):
        return Decimal(str(round(float(value), 2)))
    # Si es string, limpiar caracteres no numéricos excepto punto y coma
    text = str(value).strip()
    # Remover símbolos de moneda y espacios
    text = text.replace("$", "").replace(",", "").replace(" ", "").strip()
    # Tomar solo la parte numérica (antes de cualquier texto como "MXN")
    import re
    match = re.match(r"[\d.]+", text)
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def process_catalog(
    file_path: Path,
    column_mapping: dict,
    organization_id: uuid.UUID,
    catalog_id: uuid.UUID,
    margin_percentage: Decimal | None = None,
) -> tuple[list[dict], int]:
    """
    Procesa el Excel aplicando el mapeo confirmado por el ferretero.
    
    Retorna (productos_válidos, filas_omitidas).
    Las filas se omiten si no tienen nombre o precio válido.
    
    Args:
        file_path: ruta al Excel guardado
        column_mapping: dict con las columnas mapeadas {field: excel_column}
        organization_id: UUID de la organización
        catalog_id: UUID del catálogo recién creado
        margin_percentage: si viene de distribuidor, aplicar este % al precio
    
    Returns:
        (lista de dicts para inserción bulk, cantidad de filas omitidas)
    """
    df = pd.read_excel(file_path, header=0, engine=None)
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(how="all")

    products: list[dict] = []
    skipped = 0

    name_col = column_mapping.get("name_column")
    price_col = column_mapping.get("price_column")

    for _, row in df.iterrows():
        # ── Nombre (obligatorio) ──────────────────────────
        raw_name = row.get(name_col, "")
        if pd.isna(raw_name) or not str(raw_name).strip():
            skipped += 1
            continue
        name = str(raw_name).strip()

        # ── Precio base (obligatorio) ─────────────────────
        raw_price = row.get(price_col)
        base_price = _parse_price(raw_price)
        if base_price is None or base_price <= 0:
            skipped += 1
            continue

        # Aplicar margen de distribuidor si corresponde
        if margin_percentage is not None and margin_percentage > 0:
            multiplier = Decimal("1") + (margin_percentage / Decimal("100"))
            base_price = (base_price * multiplier).quantize(Decimal("0.01"))

        # ── Campos opcionales ─────────────────────────────
        def get_optional_str(field_key: str) -> str | None:
            col = column_mapping.get(field_key)
            if not col:
                return None
            val = row.get(col)
            if pd.isna(val):
                return None
            stripped = str(val).strip()
            return stripped if stripped else None

        def get_optional_price(field_key: str) -> Decimal | None:
            col = column_mapping.get(field_key)
            if not col:
                return None
            return _parse_price(row.get(col))

        products.append({
            "id": uuid.uuid4(),
            "catalog_id": catalog_id,
            "organization_id": organization_id,
            "name": name,
            "name_search": normalize_string(name),
            "base_price": base_price,
            "price_with_tax": get_optional_price("price_with_tax_column"),
            "product_code": get_optional_str("product_code_column"),
            "category": get_optional_str("category_column"),
            "unit": get_optional_str("unit_column"),
            "brand": get_optional_str("brand_column"),
            "description": get_optional_str("description_column"),
        })

    return products, skipped
