/*
 * Tipos TypeScript que espejean los schemas Pydantic del backend.
 *
 * ¿Por qué duplicar los tipos si ya están en el backend?
 *   TypeScript corre en el browser — no tiene acceso al código Python.
 *   Estos tipos son la "documentación en código" de qué forma tienen
 *   los datos que retorna la API. Si el backend cambia un campo,
 *   TypeScript marcará todos los lugares del frontend que lo usan.
 *
 * Convención: los nombres coinciden exactamente con los campos del backend
 * (snake_case) porque así vienen en el JSON. No los convertimos a camelCase
 * para evitar confusión entre lo que viene de la API y lo que es local.
 */

/* ── Auth ──────────────────────────────────────────────── */

export interface Organization {
  id: string
  name: string
  slug: string
}

export interface User {
  id: string
  email: string
  full_name: string
  role: string
  organization: Organization
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

/* ── Catalog ───────────────────────────────────────────── */

export interface Catalog {
  id: string
  name: string
  source_type: 'own' | 'distributor'
  distributor_name: string | null
  margin_percentage: number | null
  original_filename: string | null
  row_count: number
}

export interface ColumnMapping {
  name_column: string
  price_column: string
  price_with_tax_column?: string | null
  product_code_column?: string | null
  category_column?: string | null
  unit_column?: string | null
  brand_column?: string | null
  description_column?: string | null
}

export interface CatalogUploadResponse {
  file_key: string
  detected_columns: string[]
  suggested_mapping: Record<string, string | null>
  row_count: number
}

export interface Product {
  id: string
  name: string
  base_price: number
  price_with_tax: number | null
  product_code: string | null
  category: string | null
  unit: string | null
  brand: string | null
}

export interface ProductSearchResult {
  product: Product
  score: number
}

export interface SearchResponse {
  query: string
  results: ProductSearchResult[]
  total: number
}

/* ── Quotes ────────────────────────────────────────────── */

export type QuoteStatus = 'draft' | 'sent' | 'accepted' | 'expired'

export interface QuoteItem {
  id: string
  product_id: string | null
  product_name: string
  product_code: string | null
  unit: string | null
  quantity: number
  unit_price: number
  subtotal: number
  discount_percentage: number
}

export interface Quote {
  id: string
  quote_number: string
  client_name: string
  client_email: string | null
  client_phone: string | null
  status: QuoteStatus
  notes: string | null
  total_amount: number
  created_at: string
  updated_at: string
  items: QuoteItem[]
}

export interface QuoteListItem {
  id: string
  quote_number: string
  client_name: string
  status: QuoteStatus
  total_amount: number
  created_at: string
}

/* ── API errors ────────────────────────────────────────── */

/*
 * FastAPI retorna errores en este formato:
 *   { "detail": "Email ya registrado" }
 * o para errores de validación:
 *   { "detail": [{ "loc": [...], "msg": "...", "type": "..." }] }
 */
export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}
