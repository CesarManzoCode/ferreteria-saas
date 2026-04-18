/*
 * Página de creación de cotización.
 *
 * Flujo en esta pantalla:
 *   1. Formulario con datos del cliente → POST /quotes → se crea el quote
 *   2. Panel de búsqueda fuzzy → GET /catalogs/{id}/search
 *   3. Click en producto → POST /quotes/{id}/items
 *   4. Tabla de items con cantidad editable
 *   5. Botón PDF → GET /quotes/{id}/pdf → descarga
 *
 * Estado local del componente:
 *   phase: 'form' | 'items' — controla qué panel mostrar
 *   quote: el Quote creado (null hasta el paso 1)
 *   results: resultados del fuzzy search
 *   items: los items actuales del quote (se actualiza en cada cambio)
 */

import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Plus, Trash2, FileDown, ChevronLeft, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  createQuote, getCatalogs, searchAllCatalogs,
  addQuoteItem, deleteQuoteItem, updateQuoteItem, downloadPdf, getQuote,
} from '../api'
import { Button, Input, Textarea, Spinner, ScoreBadge, EmptyState } from '../components/ui'
import { formatCurrency } from '../lib/utils'
import { getErrorMessage } from '../api/client'
import type { Quote, Catalog, ProductSearchResult, QuoteItem } from '../types'

export default function NewQuotePage() {
  const navigate = useNavigate()

  /* ── Fase 1: formulario del cliente ─────────────────── */
  const [phase, setPhase]     = useState<'form' | 'items'>('form')
  const [creating, setCreating] = useState(false)
  const [clientForm, setClientForm] = useState({
    client_name: '', client_email: '', client_phone: '', notes: '',
  })

  /* ── Fase 2: cotización y búsqueda ──────────────────── */
  const [quote, setQuote]         = useState<Quote | null>(null)
  const [catalogs, setCatalogs]   = useState<Catalog[]>([])
  const [query, setQuery]         = useState('')
  const [results, setResults]     = useState<ProductSearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [addingId, setAddingId]   = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => { getCatalogs().then(setCatalogs) }, [])

  /* Debounce de búsqueda — espera 300ms después del último keystroke */
  useEffect(() => {
    if (!query.trim()) { setResults([]); return }
    if (searchTimeout.current) clearTimeout(searchTimeout.current)
    searchTimeout.current = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await searchAllCatalogs(query, 15)
        setResults(res.results)
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current) }
  }, [query])

  /* ── Handlers ────────────────────────────────────────── */

  async function handleCreateQuote() {
    if (!clientForm.client_name.trim()) {
      toast.error('El nombre del cliente es obligatorio')
      return
    }
    setCreating(true)
    try {
      const created = await createQuote({
        client_name:  clientForm.client_name.trim(),
        client_email: clientForm.client_email || null,
        client_phone: clientForm.client_phone || null,
        notes:        clientForm.notes        || null,
      })
      setQuote(created)
      setPhase('items')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }

  async function handleAddItem(result: ProductSearchResult) {
    if (!quote) return
    const { product } = result
    setAddingId(product.id)
    try {
      await addQuoteItem(quote.id, {
        product_id:   product.id,
        product_name: product.name,
        product_code: product.product_code,
        unit:         product.unit,
        quantity:     1,
        unit_price:   product.base_price,
      })
      /* Recargar quote completo para tener items actualizados */
      const updated = await getQuote(quote.id)
      setQuote(updated)
      toast.success(`"${product.name.slice(0, 30)}..." agregado`)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setAddingId(null)
    }
  }

  async function handleRemoveItem(itemId: string) {
    if (!quote) return
    try {
      await deleteQuoteItem(quote.id, itemId)
      setQuote(prev => prev
        ? { ...prev, items: prev.items.filter(i => i.id !== itemId) }
        : prev
      )
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  async function handleQtyChange(item: QuoteItem, qty: number) {
    if (!quote || qty < 1) return
    try {
      const updated = await updateQuoteItem(quote.id, item.id, { quantity: qty })
      setQuote(prev => {
        if (!prev) return prev
        const newTotal = prev.items.reduce((sum, i) =>
          sum + (i.id === item.id ? updated.subtotal : i.subtotal), 0)
        return {
          ...prev,
          total_amount: newTotal,
          items: prev.items.map(i => i.id === item.id ? updated : i),
        }
      })
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  async function handleDownloadPdf() {
    if (!quote) return
    if (quote.items.length === 0) {
      toast.error('Agrega al menos un producto antes de generar el PDF')
      return
    }
    setDownloading(true)
    try {
      await downloadPdf(quote.id, quote.quote_number)
      toast.success('PDF descargado')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDownloading(false)
    }
  }

  /* ── Render: Fase 1 — Formulario ─────────────────────── */
  if (phase === 'form') {
    return (
      <div className="p-6 max-w-lg mx-auto">
        <button
          onClick={() => navigate('/quotes')}
          className="flex items-center gap-1.5 text-sm text-muted hover:text-primary mb-6 transition-colors"
        >
          <ChevronLeft size={14} /> Volver
        </button>

        <h1 className="text-2xl font-medium text-primary mb-1">Nueva cotización</h1>
        <p className="text-base text-muted mb-6">Ingresa los datos del cliente para comenzar</p>

        <div className="card p-6 flex flex-col gap-4">
          <Input
            label="Nombre del cliente *"
            placeholder="Constructora ABC / Juan Martínez"
            value={clientForm.client_name}
            onChange={e => setClientForm(p => ({ ...p, client_name: e.target.value }))}
            autoFocus
          />
          <Input
            label="Correo electrónico (opcional)"
            type="email"
            placeholder="cliente@correo.com"
            value={clientForm.client_email}
            onChange={e => setClientForm(p => ({ ...p, client_email: e.target.value }))}
          />
          <Input
            label="Teléfono (opcional)"
            placeholder="331 234 5678"
            value={clientForm.client_phone}
            onChange={e => setClientForm(p => ({ ...p, client_phone: e.target.value }))}
          />
          <Textarea
            label="Notas o condiciones (opcional)"
            placeholder="Tiempo de entrega, condiciones de pago..."
            rows={3}
            value={clientForm.notes}
            onChange={e => setClientForm(p => ({ ...p, notes: e.target.value }))}
          />
          <Button
            onClick={handleCreateQuote}
            loading={creating}
            className="mt-2"
          >
            Continuar — agregar productos
          </Button>
        </div>
      </div>
    )
  }

  /* ── Render: Fase 2 — Búsqueda y items ───────────────── */
  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header con acciones */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <button
            onClick={() => navigate('/quotes')}
            className="flex items-center gap-1.5 text-sm text-muted hover:text-primary mb-1 transition-colors"
          >
            <ChevronLeft size={14} /> Cotizaciones
          </button>
          <h1 className="text-2xl font-medium text-primary">
            {quote?.quote_number} · {quote?.client_name}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => navigate(`/quotes/${quote?.id}`)}
          >
            Ver detalle
          </Button>
          <Button
            onClick={handleDownloadPdf}
            loading={downloading}
            className="bg-accent hover:bg-accent-dark text-white px-6"
          >
            <FileDown size={15} />
            Descargar PDF
          </Button>
        </div>
      </div>

      {catalogs.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-muted mb-4">No tienes catálogos cargados todavía.</p>
          <Button onClick={() => navigate('/catalogs')}>Subir catálogo</Button>
        </div>
      ) : (
        <div className="grid grid-cols-5 gap-5">
          {/* ── Panel izquierdo: búsqueda ─────────────── */}
          <div className="col-span-2 flex flex-col gap-3">
            <div className="card p-4">
              <p className="text-sm font-medium text-primary mb-3">Buscar producto</p>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  className="input pl-9"
                  placeholder="Ej: tornillo 3/4, válvula esfera..."
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  autoFocus
                />
              </div>
            </div>

            {/* Resultados */}
            <div className="card overflow-hidden flex-1">
              {searching ? (
                <div className="py-10"><Spinner /></div>
              ) : results.length === 0 ? (
                <EmptyState
                  icon={<Search size={24} />}
                  title={query ? 'Sin resultados' : 'Escribe para buscar'}
                  description={query ? 'Intenta con otras palabras.' : 'Busca en todos tus catálogos.'}
                />
              ) : (
                <div className="divide-y divide-border max-h-[520px] overflow-y-auto">
                  {results.map(({ product, score }) => (
                    <div
                      key={product.id}
                      className="flex items-center justify-between px-4 py-3 hover:bg-bg transition-colors group"
                    >
                      <div className="flex-1 min-w-0 pr-2">
                        <div className="flex items-center gap-2">
                          <p className="text-base text-primary font-medium truncate">
                            {product.name}
                          </p>
                          <ScoreBadge score={score} />
                        </div>
                        <div className="flex items-center gap-3 mt-0.5">
                          {product.product_code && (
                            <span className="text-xs text-muted">{product.product_code}</span>
                          )}
                          <span className="text-sm font-medium text-primary">
                            {formatCurrency(product.base_price)}
                          </span>
                          {product.unit && (
                            <span className="text-xs text-muted">/ {product.unit}</span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleAddItem({ product, score })}
                        disabled={addingId === product.id}
                        className="flex-shrink-0 w-7 h-7 rounded-md bg-bg border border-border
                                   flex items-center justify-center text-muted
                                   hover:bg-accent hover:border-accent hover:text-white
                                   transition-all duration-150 disabled:opacity-50"
                      >
                        {addingId === product.id
                          ? <Loader2 size={13} className="animate-spin" />
                          : <Plus size={13} />
                        }
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ── Panel derecho: items de la cotización ─── */}
          <div className="col-span-3 flex flex-col gap-3">
            <div className="card overflow-hidden flex-1">
              <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
                <p className="text-sm font-medium text-primary">
                  Productos en la cotización
                  {quote && quote.items.length > 0 && (
                    <span className="ml-2 text-muted font-normal">
                      ({quote.items.length})
                    </span>
                  )}
                </p>
              </div>

              {!quote || quote.items.length === 0 ? (
                <EmptyState
                  icon={<Plus size={24} />}
                  title="Sin productos"
                  description="Busca y agrega productos desde el panel izquierdo."
                />
              ) : (
                <>
                  {/* Header columnas */}
                  <div className="grid grid-cols-12 px-5 py-2 bg-bg border-b border-border text-xs font-medium text-muted uppercase tracking-wide">
                    <span className="col-span-5">Producto</span>
                    <span className="col-span-3 text-right">Precio</span>
                    <span className="col-span-2 text-center">Cant.</span>
                    <span className="col-span-2 text-right">Subtotal</span>
                  </div>

                  <div className="divide-y divide-border max-h-[460px] overflow-y-auto">
                    {quote.items.map(item => (
                      <div key={item.id} className="grid grid-cols-12 items-center px-5 py-3 group">
                        <div className="col-span-5 min-w-0 pr-2">
                          <p className="text-base text-primary truncate">{item.product_name}</p>
                          {item.product_code && (
                            <p className="text-xs text-muted mt-0.5">{item.product_code}</p>
                          )}
                        </div>
                        <div className="col-span-3 text-right">
                          <span className="text-base text-primary">
                            {formatCurrency(item.unit_price)}
                          </span>
                          {item.unit && (
                            <span className="text-xs text-muted ml-1">/{item.unit}</span>
                          )}
                        </div>
                        <div className="col-span-2 flex items-center justify-center">
                          <input
                            type="number"
                            min={1}
                            value={item.quantity}
                            onChange={e => handleQtyChange(item, parseInt(e.target.value) || 1)}
                            className="input w-16 text-center py-1 text-sm"
                          />
                        </div>
                        <div className="col-span-2 flex items-center justify-end gap-2">
                          <span className="text-base font-medium text-primary">
                            {formatCurrency(item.subtotal)}
                          </span>
                          <button
                            onClick={() => handleRemoveItem(item.id)}
                            className="opacity-0 group-hover:opacity-100 text-muted hover:text-danger
                                       transition-all duration-150 p-0.5"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Total */}
                  <div className="px-5 py-4 border-t border-border bg-bg flex justify-end">
                    <div className="flex items-center gap-4">
                      <span className="text-base text-muted">Total</span>
                      <span className="text-2xl font-medium text-primary">
                        {formatCurrency(quote.total_amount)}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
