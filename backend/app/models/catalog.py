"""
Modelos Catalog y Product — el corazón del sistema.

Catalog: una lista de precios subida por una ferretería.
Product: un producto dentro de esa lista.

Por qué Catalog y Product son tablas separadas y no una sola:
  Una ferretería puede tener múltiples listas de precios.
  Ejemplo: "Mi lista propia" + "Precios Truper Enero 2025" + "Precios Indar".
  Si mezclamos todo en una tabla, no podemos saber qué producto
  pertenece a qué lista, ni gestionar cada lista por separado.

source_type en Catalog:
  'own'         → el ferretero subió su propio Excel
  'distributor' → la lista viene de un distribuidor (Truper, Indar, etc.)
  
  Cuando source_type='distributor', el campo margin_percentage se activa:
  el precio final = precio_distribuidor * (1 + margin/100).
  Esto resuelve el caso de uso que mencionaste: el ferretero solo pone
  su % de ganancia y el sistema calcula el precio al cliente.

Sobre los campos opcionales en Product:
  El Excel de cada ferretería es diferente. Algunos tienen código,
  otros no. Algunos tienen categoría, otros no. Todos los campos
  que no sean nombre+precio son opcionales (nullable=True).
  El mapeo de columnas en el frontend decide qué se llena.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Catalog(Base, UUIDMixin, TimestampMixin):
    """
    Lista de precios de una organización.
    
    row_count: cuántos productos tiene. Se calcula al procesar el Excel
               y se guarda para no tener que hacer COUNT(*) cada vez.
    
    original_filename: guardamos el nombre del archivo original para
                       mostrárselo al usuario ("Tu archivo: lista_truper.xlsx").
    """
    __tablename__ = "catalogs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50),
        default="own",
        nullable=False,
        comment="'own' para lista propia, 'distributor' para lista de distribuidor",
    )
    distributor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    margin_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Margen aplicado sobre precio de distribuidor. Ej: 20.00 = 20%",
    )
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="catalogs")
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="catalog",
        cascade="all, delete-orphan",  # si se borra el catálogo, se borran sus productos
    )

    def __repr__(self) -> str:
        return f"<Catalog id={self.id} name={self.name!r} source={self.source_type!r}>"


class Product(Base, UUIDMixin, TimestampMixin):
    """
    Producto dentro de un catálogo.
    
    Sobre Numeric vs Float para precios:
      Float es un número de punto flotante binario — tiene errores de
      precisión. 0.1 + 0.2 en float puede dar 0.30000000000000004.
      Para dinero SIEMPRE se usa Numeric/Decimal, que es precisión exacta.
      Numeric(12, 2) = hasta 999,999,999.99 con 2 decimales.
    
    name_search: versión normalizada del nombre para búsqueda fuzzy.
      Se guarda en minúsculas y sin caracteres especiales.
      RapidFuzz compara contra este campo, no contra el nombre original.
      Eso mejora mucho la calidad de los resultados.
    
    unit: "pieza", "metro", "litro", "kilo" — los ferreteros venden
      en distintas unidades. Null si no aplica.
    """
    __tablename__ = "products"

    catalog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Desnormalización intencional: evita JOINs innecesarios en búsquedas",
    )

    # Campos obligatorios — toda lista de precios tiene al menos esto
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_search: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Nombre normalizado para búsqueda fuzzy (lowercase, sin acentos)",
    )
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Campos opcionales — dependen del Excel del ferretero
    price_with_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)

    catalog: Mapped["Catalog"] = relationship("Catalog", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} price={self.base_price}>"
