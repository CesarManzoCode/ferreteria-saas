import { apiClient } from './client'
import type {
  Catalog, CatalogUploadResponse, ColumnMapping,
  SearchResponse, Quote, QuoteItem, QuoteListItem,
} from '../types'

/* ── Catálogos ─────────────────────────────────────────── */

export async function uploadExcel(file: File): Promise<CatalogUploadResponse> {
  /*
   * FormData es necesario para subir archivos — no se puede hacer con JSON.
   * axios detecta automáticamente que es FormData y pone el
   * Content-Type correcto (multipart/form-data con el boundary).
   */
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<CatalogUploadResponse>(
    '/api/v1/catalogs/upload',
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

export interface ProcessCatalogPayload {
  file_key: string
  catalog_name: string
  column_mapping: ColumnMapping
  source_type?: 'own' | 'distributor'
  distributor_name?: string | null
  margin_percentage?: number | null
}

export async function processCatalog(payload: ProcessCatalogPayload): Promise<Catalog> {
  const { data } = await apiClient.post<Catalog>('/api/v1/catalogs/process', payload)
  return data
}

export async function getCatalogs(): Promise<Catalog[]> {
  const { data } = await apiClient.get<Catalog[]>('/api/v1/catalogs/')
  return data
}

export async function deleteCatalog(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/catalogs/${id}`)
}

export async function searchProducts(
  catalogId: string,
  query: string,
  limit = 20
): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>(
    `/api/v1/catalogs/${catalogId}/search`,
    { params: { q: query, limit } }
  )
  return data
}

export async function searchAllCatalogs(query: string, limit = 20): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>(
    '/api/v1/catalogs/search/all',
    { params: { q: query, limit } }
  )
  return data
}

/* ── Cotizaciones ──────────────────────────────────────── */

export interface CreateQuotePayload {
  client_name: string
  client_email?: string | null
  client_phone?: string | null
  notes?: string | null
}

export async function createQuote(payload: CreateQuotePayload): Promise<Quote> {
  const { data } = await apiClient.post<Quote>('/api/v1/quotes/', payload)
  return data
}

export async function getQuotes(status?: string): Promise<QuoteListItem[]> {
  const { data } = await apiClient.get<QuoteListItem[]>('/api/v1/quotes/', {
    params: status ? { status_filter: status } : {}
  })
  return data
}

export async function getQuote(id: string): Promise<Quote> {
  const { data } = await apiClient.get<Quote>(`/api/v1/quotes/${id}`)
  return data
}

export async function updateQuote(id: string, payload: Partial<CreateQuotePayload & { status: string }>): Promise<Quote> {
  const { data } = await apiClient.patch<Quote>(`/api/v1/quotes/${id}`, payload)
  return data
}

export async function deleteQuote(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/quotes/${id}`)
}

export interface AddItemPayload {
  product_id?: string | null
  product_name: string
  product_code?: string | null
  unit?: string | null
  quantity: number
  unit_price: number
  discount_percentage?: number
}

export async function addQuoteItem(quoteId: string, payload: AddItemPayload): Promise<QuoteItem> {
  const { data } = await apiClient.post<QuoteItem>(`/api/v1/quotes/${quoteId}/items`, payload)
  return data
}

export async function updateQuoteItem(
  quoteId: string,
  itemId: string,
  payload: { quantity?: number; unit_price?: number; discount_percentage?: number }
): Promise<QuoteItem> {
  const { data } = await apiClient.patch<QuoteItem>(
    `/api/v1/quotes/${quoteId}/items/${itemId}`,
    payload
  )
  return data
}

export async function deleteQuoteItem(quoteId: string, itemId: string): Promise<void> {
  await apiClient.delete(`/api/v1/quotes/${quoteId}/items/${itemId}`)
}

/*
 * Descarga el PDF — no es un JSON, es un blob (datos binarios).
 * Creamos un <a> temporal, lo "clickeamos" programáticamente
 * y lo removemos. Así el browser descarga el archivo sin
 * abrir una nueva pestaña.
 */
export async function downloadPdf(quoteId: string, quoteNumber: string): Promise<void> {
  const response = await apiClient.get(`/api/v1/quotes/${quoteId}/pdf`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `${quoteNumber}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
