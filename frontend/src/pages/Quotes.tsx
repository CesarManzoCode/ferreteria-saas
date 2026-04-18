import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FileText, Search } from 'lucide-react'
import toast from 'react-hot-toast'
import { getQuotes, deleteQuote } from '../api'
import { Button, Spinner, EmptyState, Badge } from '../components/ui'
import { formatCurrency, formatDate, QUOTE_STATUS_LABELS, QUOTE_STATUS_CLASS } from '../lib/utils'
import { getErrorMessage } from '../api/client'
import type { QuoteListItem } from '../types'

const STATUS_FILTERS = [
  { value: '',         label: 'Todas' },
  { value: 'draft',    label: 'Borradores' },
  { value: 'sent',     label: 'Enviadas' },
  { value: 'accepted', label: 'Aceptadas' },
  { value: 'expired',  label: 'Vencidas' },
]

export default function QuotesPage() {
  const navigate = useNavigate()
  const [quotes, setQuotes]         = useState<QuoteListItem[]>([])
  const [loading, setLoading]       = useState(true)
  const [statusFilter, setStatus]   = useState('')
  const [search, setSearch]         = useState('')
  const [deleting, setDeleting]     = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const data = await getQuotes(statusFilter || undefined)
      setQuotes(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [statusFilter])

  async function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation()
    if (!confirm('¿Eliminar esta cotización? Esta acción no se puede deshacer.')) return
    setDeleting(id)
    try {
      await deleteQuote(id)
      setQuotes(prev => prev.filter(q => q.id !== id))
      toast.success('Cotización eliminada')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setDeleting(null)
    }
  }

  const filtered = quotes.filter(q =>
    q.client_name.toLowerCase().includes(search.toLowerCase()) ||
    q.quote_number.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-medium text-primary">Cotizaciones</h1>
        <Button onClick={() => navigate('/quotes/new')}>
          <Plus size={15} /> Nueva cotización
        </Button>
      </div>

      {/* Filtros y búsqueda */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            className="input pl-9"
            placeholder="Buscar por cliente o número..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-1">
          {STATUS_FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setStatus(f.value)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150
                ${statusFilter === f.value
                  ? 'bg-primary text-white'
                  : 'bg-surface border border-border text-primary hover:bg-bg'}`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Lista */}
      <div className="card overflow-hidden">
        {/* Encabezado de tabla */}
        <div className="grid grid-cols-12 px-5 py-2.5 bg-bg border-b border-border text-xs font-medium text-muted uppercase tracking-wide">
          <span className="col-span-2">Número</span>
          <span className="col-span-4">Cliente</span>
          <span className="col-span-2">Estado</span>
          <span className="col-span-2">Fecha</span>
          <span className="col-span-2 text-right">Total</span>
        </div>

        {loading ? (
          <div className="py-16"><Spinner size={24} /></div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<FileText size={32} />}
            title="Sin cotizaciones"
            description={search ? 'Ninguna cotización coincide con tu búsqueda.' : 'Crea tu primera cotización para empezar.'}
            action={!search ? <Button onClick={() => navigate('/quotes/new')}><Plus size={14} />Nueva cotización</Button> : undefined}
          />
        ) : (
          <div className="divide-y divide-border">
            {filtered.map(quote => (
              <div
                key={quote.id}
                onClick={() => navigate(`/quotes/${quote.id}`)}
                className="grid grid-cols-12 items-center px-5 py-3.5
                           hover:bg-bg cursor-pointer transition-colors duration-100 group"
              >
                <span className="col-span-2 text-sm font-medium text-primary">
                  {quote.quote_number}
                </span>
                <span className="col-span-4 text-base text-primary truncate pr-4">
                  {quote.client_name}
                </span>
                <span className="col-span-2">
                  <Badge status={quote.status} label={QUOTE_STATUS_LABELS[quote.status]} />
                </span>
                <span className="col-span-2 text-sm text-muted">
                  {formatDate(quote.created_at)}
                </span>
                <div className="col-span-2 flex items-center justify-end gap-3">
                  <span className="text-base font-medium text-primary">
                    {formatCurrency(quote.total_amount)}
                  </span>
                  <button
                    onClick={e => handleDelete(e, quote.id)}
                    disabled={deleting === quote.id}
                    className="opacity-0 group-hover:opacity-100 text-xs text-muted
                               hover:text-danger transition-all duration-150 px-1"
                  >
                    {deleting === quote.id ? '...' : 'Eliminar'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
