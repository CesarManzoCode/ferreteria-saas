"""
Servicio de búsqueda fuzzy sobre productos.

¿Por qué un servicio separado para búsqueda?
  La búsqueda tiene su propia lógica no trivial:
    - Cargar productos de la DB en memoria
    - Normalizar el query del usuario
    - Correr RapidFuzz
    - Filtrar por threshold
    - Ordenar por score
    - Paginar resultados
  
  Si esto viviera en el endpoint directamente, el endpoint tendría
  demasiada responsabilidad. Separarlo permite testear la lógica
  de búsqueda independientemente del HTTP.

Estrategia de búsqueda:
  1. Cargar todos los name_search de la organización en un array
  2. Normalizar el query del usuario con la misma función usada al indexar
  3. RapidFuzz compara el query contra todos los name_search
  4. Filtrar resultados con score >= threshold
  5. Retornar los top N ordenados por score

¿Por qué cargar TODO en memoria?
  Para el tamaño de ferreterías pequeñas/medianas (1,000-30,000 productos),
  un array de strings en Python ocupa ~10-30 MB de RAM. Es perfectamente
  manejable. La alternativa (query a DB + pg_trgm) es más compleja
  de configurar y no necesaria a esta escala.

  Si en el futuro una ferretería tiene 200,000 productos, migrar a
  pg_trgm es un cambio en este servicio únicamente.
"""

from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.schemas.catalog import ProductResponse, ProductSearchResult, SearchResponse
from app.services.excel_service import normalize_string

# Importamos process de rapidfuzz (no fuzz directamente)
# process.extract es más conveniente para buscar contra una lista
from rapidfuzz import process as fuzz_process
from rapidfuzz import fuzz


def search_products(
    db: Session,
    organization_id,
    query: str,
    catalog_id=None,
    threshold: float = 55.0,
    limit: int = 20,
) -> SearchResponse:
    """
    Busca productos usando fuzzy matching sobre name_search.
    
    Args:
        db: sesión de base de datos
        organization_id: UUID de la organización (multi-tenant)
        query: texto que el ferretero escribió en el buscador
        catalog_id: si se da, busca solo en ese catálogo;
                    si es None, busca en todos los catálogos de la org
        threshold: score mínimo para incluir un resultado (0-100)
                   55 es un buen balance — evita falsos positivos
                   pero permite typos y abreviaciones
        limit: máximo de resultados a retornar
    
    Returns:
        SearchResponse con los resultados ordenados por score descendente
    """
    if not query.strip():
        return SearchResponse(query=query, results=[], total=0)

    # ── 1. Cargar productos de la DB ──────────────────────
    # Solo cargamos id + name_search para el matching,
    # no todos los campos — menos datos en memoria
    db_query = db.query(Product).filter(
        Product.organization_id == organization_id
    )
    if catalog_id is not None:
        db_query = db_query.filter(Product.catalog_id == catalog_id)

    products = db_query.all()

    if not products:
        return SearchResponse(query=query, results=[], total=0)

    # ── 2. Preparar estructuras para RapidFuzz ────────────
    # RapidFuzz necesita una lista de strings para buscar
    # y retorna índices — los usamos para recuperar el objeto completo
    search_strings = [p.name_search for p in products]
    normalized_query = normalize_string(query)

    # ── 3. Búsqueda fuzzy ─────────────────────────────────
    # fuzz_process.extract retorna: [(string, score, index), ...]
    # WRatio combina múltiples algoritmos — mejor para búsquedas generales:
    #   - partial_ratio: query contenido dentro del string
    #   - token_sort_ratio: ignora orden de palabras
    #   - token_set_ratio: ignora palabras repetidas
    raw_results = fuzz_process.extract(
        normalized_query,
        search_strings,
        scorer=fuzz.WRatio,
        score_cutoff=threshold,
        limit=limit,
    )

    if not raw_results:
        return SearchResponse(query=query, results=[], total=0)

    # ── 4. Construir respuesta ────────────────────────────
    # raw_results viene ordenado por score descendente — ya está ordenado
    results: list[ProductSearchResult] = []
    for _matched_string, score, index in raw_results:
        product = products[index]
        results.append(
            ProductSearchResult(
                product=ProductResponse.model_validate(product),
                score=round(score, 1),
            )
        )

    return SearchResponse(
        query=query,
        results=results,
        total=len(results),
    )
