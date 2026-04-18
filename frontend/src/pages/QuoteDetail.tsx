import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, FileDown, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { getQuote, downloadPdf, deleteQuote } from '../api'
import { Button, Spinner, Badge } from '../components/ui'
import { formatCurrency, formatDateLong, QUOTE_STATUS_LABELS } from '../lib/utils'
import { getErrorMessage } from '../api/client'
import type { Quote } from '../types'

export default function QuoteDetailPage() {
  const { id }       = useParams<{ id: string }>()
  const navigate     = useNavigate()
  const [quote, setQuote]         = useState<Quote | null>(null)
  const [loading, setLoading]     = useState(true)
  const [downloading, setDown]    = useState(false)
  const [deleting, setDeleting]   = useState(false)

  useEffect(() => {
    if (!id) return
    getQuote(id)
      .then(setQuote)
      .catch(() => { toast.error('No se pudo cargar la cotización'); navigate('/quotes') })
      .finally(() => setLoading(false))
  }, [id])

  async function handleDownload() {
    if (!quote) return
    setDown(true)
    try {
      await downloadPdf(quote.id, quote.quote_number)
      toast.success('PDF descargado')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDown(false)
    }
  }

  async function handleDelete() {
    if (!quote) return
    if (!confirm(`¿Eliminar la cotización ${quote.quote_number}? Esta acción no se puede deshacer.`)) return
    setDeleting(true)
    try {
      await deleteQuote(quote.id)
      toast.success('Cotización eliminada')
      navigate('/quotes')
    } catch (err) {
      toast.error(getErrorMessage(err))
      setDeleting(false)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64"><Spinner size={28} /></div>
  if (!quote)  return null

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Breadcrumb */}
      <button
        onClick={() => navigate('/quotes')}
        className="flex items-center gap-1.5 text-sm text-muted hover:text-primary mb-5 transition-colors"
      >
        <ChevronLeft size={14} /> Cotizaciones
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-medium text-primary">{quote.quote_number}</h1>
            <Badge status={quote.status} label={QUOTE_STATUS_LABELS[quote.status]} />
          </div>
          <p className="text-base text-muted">
            Creada el {formatDateLong(quote.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="danger" onClick={handleDelete} loading={deleting}>
            <Trash2 size={14} />
            Eliminar
          </Button>
          <Button onClick={handleDownload} loading={downloading} className="px-5">
            <FileDown size={15} />
            Descargar PDF
          </Button>
        </div>
      </div>

      {/* Info del cliente */}
      <div className="card p-5 mb-4">
        <p className="text-xs font-medium text-muted uppercase tracking-wide mb-3">Cliente</p>
        <p className="text-lg font-medium text-primary">{quote.client_name}</p>
        {quote.client_email && <p className="text-base text-muted mt-0.5">{quote.client_email}</p>}
        {quote.client_phone && <p className="text-base text-muted">{quote.client_phone}</p>}
        {quote.notes && (
          <div className="mt-3 pt-3 border-t border-border">
            <p className="text-xs font-medium text-muted uppercase tracking-wide mb-1">Notas</p>
            <p className="text-base text-primary">{quote.notes}</p>
          </div>
        )}
      </div>

      {/* Tabla de productos */}
      <div className="card overflow-hidden mb-4">
        <div className="px-5 py-3 border-b border-border bg-bg">
          <p className="text-sm font-medium text-primary">Productos ({quote.items.length})</p>
        </div>

        {/* Header */}
        <div className="grid grid-cols-12 px-5 py-2.5 border-b border-border text-xs font-medium text-muted uppercase tracking-wide">
          <span className="col-span-5">Producto</span>
          <span className="col-span-2 text-center">Cant.</span>
          <span className="col-span-2 text-right">Precio unit.</span>
          <span className="col-span-3 text-right">Subtotal</span>
        </div>

        <div className="divide-y divide-border">
          {quote.items.map(item => (
            <div key={item.id} className="grid grid-cols-12 items-center px-5 py-3.5">
              <div className="col-span-5">
                <p className="text-base text-primary">{item.product_name}</p>
                <div className="flex items-center gap-3 mt-0.5">
                  {item.product_code && <span className="text-xs text-muted">{item.product_code}</span>}
                  {item.unit && <span className="text-xs text-muted">{item.unit}</span>}
                  {item.discount_percentage > 0 && (
                    <span className="text-xs font-medium text-warning bg-warning-light px-1.5 py-0.5 rounded">
                      -{item.discount_percentage}% dto.
                    </span>
                  )}
                </div>
              </div>
              <span className="col-span-2 text-base text-primary text-center">{item.quantity}</span>
              <span className="col-span-2 text-base text-primary text-right">
                {formatCurrency(item.unit_price)}
              </span>
              <span className="col-span-3 text-base font-medium text-primary text-right">
                {formatCurrency(item.subtotal)}
              </span>
            </div>
          ))}
        </div>

        {/* Total */}
        <div className="px-5 py-4 border-t-2 border-border bg-bg flex justify-end items-center gap-4">
          <span className="text-base text-muted">Total</span>
          <span className="text-2xl font-medium text-primary">
            {formatCurrency(quote.total_amount)}
          </span>
        </div>
      </div>

      {/* CTA PDF prominente */}
      {quote.items.length > 0 && (
        <div className="card p-5 flex items-center justify-between bg-primary border-primary">
          <div>
            <p className="text-white font-medium">¿Lista para enviar al cliente?</p>
            <p className="text-white/60 text-sm mt-0.5">Descarga el PDF y compártelo por WhatsApp o correo.</p>
          </div>
          <Button
            onClick={handleDownload}
            loading={downloading}
            className="bg-accent hover:bg-accent-dark text-white px-6 flex-shrink-0"
          >
            <FileDown size={15} />
            Descargar PDF
          </Button>
        </div>
      )}
    </div>
  )
}
