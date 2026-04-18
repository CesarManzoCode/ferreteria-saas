import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, BookOpen, Plus, TrendingUp } from 'lucide-react'
import { getQuotes } from '../api'
import { getCatalogs } from '../api'
import { useAuth } from '../hooks/useAuth'
import { Button, Spinner } from '../components/ui'
import { formatCurrency, formatDate, QUOTE_STATUS_LABELS, QUOTE_STATUS_CLASS } from '../lib/utils'
import type { QuoteListItem, Catalog } from '../types'

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [quotes, setQuotes]     = useState<QuoteListItem[]>([])
  const [catalogs, setCatalogs] = useState<Catalog[]>([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [q, c] = await Promise.all([getQuotes(), getCatalogs()])
        setQuotes(q)
        setCatalogs(c)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const totalProducts = catalogs.reduce((sum, c) => sum + c.row_count, 0)
  const sentQuotes    = quotes.filter(q => q.status === 'sent' || q.status === 'accepted')
  const totalRevenue  = sentQuotes.reduce((sum, q) => sum + q.total_amount, 0)
  const recentQuotes  = quotes.slice(0, 5)

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Spinner size={28} />
    </div>
  )

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-medium text-primary">
            Hola, {user?.full_name.split(' ')[0]}
          </h1>
          <p className="text-base text-muted mt-0.5">
            {user?.organization.name}
          </p>
        </div>
        <Button onClick={() => navigate('/quotes/new')}>
          <Plus size={15} />
          Nueva cotización
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <FileText size={14} className="text-muted" />
            <span className="text-sm text-muted">Cotizaciones</span>
          </div>
          <p className="text-3xl font-medium text-primary">{quotes.length}</p>
          <p className="text-xs text-muted mt-1">{sentQuotes.length} enviadas</p>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen size={14} className="text-muted" />
            <span className="text-sm text-muted">Productos</span>
          </div>
          <p className="text-3xl font-medium text-primary">
            {totalProducts.toLocaleString('es-MX')}
          </p>
          <p className="text-xs text-muted mt-1">{catalogs.length} catálogos</p>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={14} className="text-muted" />
            <span className="text-sm text-muted">Total cotizado</span>
          </div>
          <p className="text-3xl font-medium text-primary">
            {formatCurrency(totalRevenue)}
          </p>
          <p className="text-xs text-muted mt-1">en cotizaciones enviadas</p>
        </div>
      </div>

      {/* Cotizaciones recientes */}
      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="text-lg font-medium text-primary">Cotizaciones recientes</h2>
          <button
            onClick={() => navigate('/quotes')}
            className="text-sm text-accent hover:underline"
          >
            Ver todas
          </button>
        </div>

        {recentQuotes.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <p className="text-muted text-base mb-4">Aún no tienes cotizaciones</p>
            <Button onClick={() => navigate('/quotes/new')}>
              <Plus size={14} />
              Crear primera cotización
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {recentQuotes.map(quote => (
              <button
                key={quote.id}
                onClick={() => navigate(`/quotes/${quote.id}`)}
                className="w-full flex items-center justify-between px-5 py-3.5
                           hover:bg-bg transition-colors duration-100 text-left"
              >
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-primary w-20">
                    {quote.quote_number}
                  </span>
                  <span className="text-base text-primary">{quote.client_name}</span>
                  <span className={`badge ${QUOTE_STATUS_CLASS[quote.status]}`}>
                    {QUOTE_STATUS_LABELS[quote.status]}
                  </span>
                </div>
                <div className="flex items-center gap-6">
                  <span className="text-sm text-muted">{formatDate(quote.created_at)}</span>
                  <span className="text-base font-medium text-primary w-28 text-right">
                    {formatCurrency(quote.total_amount)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
