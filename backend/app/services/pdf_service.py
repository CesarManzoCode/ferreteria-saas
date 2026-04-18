"""
Servicio de generación de PDF para cotizaciones.

¿Por qué HTML → PDF en lugar de dibujar el PDF directamente?
  Librerías como ReportLab o fpdf2 generan PDF dibujando elemento
  por elemento: "texto en posición x=100, y=200, fuente Arial 12pt".
  Eso es muy verboso y difícil de mantener — cambiar el diseño
  requiere recalcular posiciones manualmente.

  WeasyPrint toma HTML+CSS y lo renderiza como PDF. Ventajas:
    - El template es HTML que cualquiera puede leer y modificar
    - CSS maneja el layout — no tienes que calcular posiciones
    - Puedes previsualizar el template en el browser antes de generar
    - Cambiar el diseño es cambiar CSS, no recalcular coordenadas

Jinja2:
  Motor de templates. Recibe un string con {{ variables }} y { % lógica % }
  y lo rellena con datos Python. Es el mismo que usa Flask y Django.
  
  Template: "Total: {{ quote.total_amount | format_currency }}"
  Datos:    quote.total_amount = Decimal("1500.00")
  Resultado: "Total: $1,500.00"

Diseño del PDF:
  El PDF tiene que verse profesional — eso es parte del valor del producto.
  Un ferretero que le da a su cliente un PDF bien formateado con el logo
  de su negocio se ve más serio que uno que manda una foto de papel.
  El template incluye:
    - Header con nombre de la ferretería y número de cotización
    - Tabla de productos con columnas alineadas
    - Total destacado
    - Fecha y condiciones
"""

from datetime import datetime
from decimal import Decimal

from jinja2 import DictLoader, Environment

from app.models.quote import Quote

# ── Template HTML del PDF ─────────────────────────────────
# Está definido aquí como string para mantener todo en un solo archivo.
# En el futuro puede moverse a un archivo .html externo.

PDF_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 11px;
    color: #1a1a2e;
    padding: 30px 40px;
  }

  /* ── Header ── */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 20px;
    border-bottom: 3px solid #1a1a2e;
    margin-bottom: 24px;
  }

  .company-name {
    font-size: 22px;
    font-weight: 800;
    color: #1a1a2e;
    letter-spacing: -0.5px;
  }

  .quote-meta {
    text-align: right;
  }

  .quote-number {
    font-size: 18px;
    font-weight: 700;
    color: #e84545;
  }

  .quote-date {
    color: #666;
    margin-top: 4px;
    font-size: 10px;
  }

  /* ── Info cliente ── */
  .client-section {
    background: #f8f9fc;
    border-left: 4px solid #e84545;
    padding: 12px 16px;
    margin-bottom: 24px;
    border-radius: 0 4px 4px 0;
  }

  .section-label {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #999;
    margin-bottom: 4px;
  }

  .client-name {
    font-size: 14px;
    font-weight: 700;
  }

  .client-contact {
    color: #555;
    margin-top: 2px;
    font-size: 10px;
  }

  /* ── Tabla de productos ── */
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 24px;
  }

  thead tr {
    background: #1a1a2e;
    color: white;
  }

  thead th {
    padding: 10px 12px;
    text-align: left;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }

  thead th.right { text-align: right; }

  tbody tr {
    border-bottom: 1px solid #eee;
  }

  tbody tr:nth-child(even) {
    background: #fafafa;
  }

  tbody td {
    padding: 9px 12px;
    vertical-align: top;
  }

  .product-name { font-weight: 600; }
  .product-code { color: #888; font-size: 9px; margin-top: 2px; }

  .td-right { text-align: right; }
  .td-center { text-align: center; }

  .discount-badge {
    background: #fff3cd;
    color: #856404;
    font-size: 8px;
    padding: 1px 5px;
    border-radius: 3px;
    margin-left: 4px;
  }

  /* ── Totales ── */
  .totals-section {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 24px;
  }

  .totals-box {
    width: 260px;
  }

  .total-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #eee;
    font-size: 11px;
  }

  .total-row.grand {
    border-top: 2px solid #1a1a2e;
    border-bottom: none;
    padding-top: 10px;
    margin-top: 4px;
    font-size: 15px;
    font-weight: 800;
    color: #1a1a2e;
  }

  .total-label { color: #555; }

  /* ── Notas ── */
  .notes-section {
    background: #f8f9fc;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 24px;
  }

  /* ── Footer ── */
  .footer {
    text-align: center;
    color: #aaa;
    font-size: 9px;
    padding-top: 16px;
    border-top: 1px solid #eee;
  }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div>
    <div class="company-name">{{ org_name }}</div>
  </div>
  <div class="quote-meta">
    <div class="quote-number">{{ quote.quote_number }}</div>
    <div class="quote-date">Fecha: {{ quote.created_at | format_date }}</div>
    <div class="quote-date">Válida por 15 días</div>
  </div>
</div>

<!-- Cliente -->
<div class="client-section">
  <div class="section-label">Cliente</div>
  <div class="client-name">{{ quote.client_name }}</div>
  {% if quote.client_email or quote.client_phone %}
  <div class="client-contact">
    {% if quote.client_email %}{{ quote.client_email }}{% endif %}
    {% if quote.client_email and quote.client_phone %} · {% endif %}
    {% if quote.client_phone %}{{ quote.client_phone }}{% endif %}
  </div>
  {% endif %}
</div>

<!-- Tabla de productos -->
<table>
  <thead>
    <tr>
      <th style="width: 40%">Producto</th>
      <th style="width: 12%">Clave</th>
      <th style="width: 8%">Unidad</th>
      <th class="right" style="width: 10%">Cant.</th>
      <th class="right" style="width: 15%">P. Unitario</th>
      <th class="right" style="width: 15%">Subtotal</th>
    </tr>
  </thead>
  <tbody>
    {% for item in quote.items %}
    <tr>
      <td>
        <div class="product-name">
          {{ item.product_name }}
          {% if item.discount_percentage > 0 %}
          <span class="discount-badge">-{{ item.discount_percentage }}%</span>
          {% endif %}
        </div>
      </td>
      <td>
        {% if item.product_code %}
        <div class="product-code">{{ item.product_code }}</div>
        {% else %}—{% endif %}
      </td>
      <td>{{ item.unit or '—' }}</td>
      <td class="td-right">{{ item.quantity }}</td>
      <td class="td-right">{{ item.unit_price | format_currency }}</td>
      <td class="td-right"><strong>{{ item.subtotal | format_currency }}</strong></td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<!-- Totales -->
<div class="totals-section">
  <div class="totals-box">
    <div class="total-row">
      <span class="total-label">Subtotal</span>
      <span>{{ subtotal | format_currency }}</span>
    </div>
    <div class="total-row grand">
      <span>Total</span>
      <span>{{ quote.total_amount | format_currency }}</span>
    </div>
  </div>
</div>

<!-- Notas -->
{% if quote.notes %}
<div class="notes-section">
  <div class="section-label">Notas y condiciones</div>
  <p style="margin-top: 6px; color: #444; line-height: 1.5;">{{ quote.notes }}</p>
</div>
{% endif %}

<!-- Footer -->
<div class="footer">
  Cotización generada el {{ now | format_date }} · {{ org_name }} · Documento no fiscal
</div>

</body>
</html>
"""


def _format_currency(value: Decimal | float) -> str:
    """Formatea un Decimal como precio en MXN: $1,500.00"""
    return f"${float(value):,.2f}"


def _format_date(value: datetime) -> str:
    """Formatea fecha como: 15 de enero de 2025"""
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    return f"{value.day} de {meses[value.month - 1]} de {value.year}"


def generate_quote_pdf(quote: Quote, org_name: str) -> bytes:
    """
    Genera el PDF de una cotización y lo retorna como bytes.

    Args:
        quote: objeto Quote con sus items cargados (joinedload)
        org_name: nombre de la organización para el header del PDF

    Returns:
        bytes del PDF listo para enviar como response HTTP

    WeasyPrint instala chromium internamente para renderizar — por eso
    el Dockerfile instala libpango y libcairo (dependencias de renderizado).
    """
    # Configurar Jinja2 con los filtros personalizados
    env = Environment(loader=DictLoader({"quote.html": PDF_TEMPLATE}))
    env.filters["format_currency"] = _format_currency
    env.filters["format_date"] = _format_date

    # Calcular subtotal (antes de cualquier descuento global futuro)
    subtotal = sum(item.subtotal for item in quote.items)

    # Renderizar HTML con los datos de la cotización
    template = env.get_template("quote.html")
    html_content = template.render(
        quote=quote,
        org_name=org_name,
        subtotal=subtotal,
        now=datetime.now(),
    )

    # Convertir HTML a PDF con WeasyPrint
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
    except Exception as e:
        raise RuntimeError(f"Error generando PDF: {e}") from e

    return pdf_bytes
