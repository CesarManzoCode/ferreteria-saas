import { useState, useEffect } from 'react'
import { Users, Building2, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiClient } from '../api/client'
import { Spinner, EmptyState } from '../components/ui'
import { formatDate, formatDateLong } from '../lib/utils'
import { getErrorMessage } from '../api/client'

interface OrgView {
  id: string
  name: string
  slug: string
  is_active: boolean
  subscription_status: string
  trial_ends_at: string | null
  subscribed_at: string | null
  admin_notes: string | null
  created_at: string
  user_count: number
  catalog_count: number
  quote_count: number
}

interface Stats {
  total_organizations: number
  trial_organizations: number
  active_organizations: number
  expired_organizations: number
  total_users: number
  total_quotes: number
}

const STATUS_LABEL: Record<string, string> = {
  trial: 'En prueba', active: 'Activa', expired: 'Vencida',
}
const STATUS_CLASS: Record<string, string> = {
  trial:   'bg-warning-light text-warning',
  active:  'bg-success-light text-success',
  expired: 'bg-danger-light text-danger',
}

export default function AdminPage() {
  const [stats, setStats]   = useState<Stats | null>(null)
  const [orgs, setOrgs]     = useState<OrgView[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<OrgView | null>(null)
  const [notes, setNotes]   = useState('')
  const [saving, setSaving] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const [s, o] = await Promise.all([
        apiClient.get<Stats>('/api/v1/admin/stats'),
        apiClient.get<OrgView[]>('/api/v1/admin/organizations'),
      ])
      setStats(s.data)
      setOrgs(o.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleSetStatus(orgId: string, newStatus: string) {
    setSaving(true)
    try {
      const { data } = await apiClient.patch<OrgView>(
        `/api/v1/admin/organizations/${orgId}/subscription`,
        { subscription_status: newStatus, admin_notes: notes || undefined }
      )
      setOrgs(prev => prev.map(o => o.id === orgId ? data : o))
      setSelected(data)
      setNotes('')
      toast.success(`Estado cambiado a: ${STATUS_LABEL[newStatus]}`)
      load()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleToggleActive(orgId: string) {
    try {
      const { data } = await apiClient.patch<OrgView>(
        `/api/v1/admin/organizations/${orgId}/toggle-active`, {}
      )
      setOrgs(prev => prev.map(o => o.id === orgId ? data : o))
      setSelected(data)
      toast.success(data.is_active ? 'Cuenta activada' : 'Cuenta desactivada')
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner size={28} /></div>

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-medium text-primary mb-6">Panel de administración</h1>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Total organizaciones', value: stats.total_organizations, icon: Building2 },
            { label: 'En prueba',            value: stats.trial_organizations,   icon: Clock },
            { label: 'Activas (pagando)',    value: stats.active_organizations,  icon: CheckCircle },
            { label: 'Vencidas',            value: stats.expired_organizations, icon: XCircle },
            { label: 'Usuarios totales',    value: stats.total_users,           icon: Users },
            { label: 'Cotizaciones totales',value: stats.total_quotes,          icon: TrendingUp },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="card p-4">
              <div className="flex items-center gap-2 mb-1">
                <Icon size={13} className="text-muted" />
                <span className="text-sm text-muted">{label}</span>
              </div>
              <p className="text-3xl font-medium text-primary">{value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-5 gap-5">
        {/* Lista de orgs */}
        <div className="col-span-3 card overflow-hidden">
          <div className="px-5 py-3.5 border-b border-border bg-bg">
            <p className="text-sm font-medium text-primary">Ferreterías registradas</p>
          </div>
          {orgs.length === 0 ? (
            <EmptyState icon={<Building2 size={24} />} title="Sin organizaciones" />
          ) : (
            <div className="divide-y divide-border max-h-[520px] overflow-y-auto">
              {orgs.map(org => (
                <button
                  key={org.id}
                  onClick={() => { setSelected(org); setNotes(org.admin_notes || '') }}
                  className={`w-full flex items-center justify-between px-5 py-3.5
                              hover:bg-bg transition-colors text-left
                              ${selected?.id === org.id ? 'bg-bg border-l-2 border-l-accent' : ''}`}
                >
                  <div>
                    <p className="text-base font-medium text-primary">{org.name}</p>
                    <p className="text-xs text-muted mt-0.5">
                      {org.user_count} usuarios · {org.quote_count} cotizaciones · desde {formatDate(org.created_at)}
                    </p>
                  </div>
                  <span className={`badge text-xs px-2 py-0.5 rounded ${STATUS_CLASS[org.subscription_status]}`}>
                    {STATUS_LABEL[org.subscription_status]}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detalle de org seleccionada */}
        <div className="col-span-2">
          {!selected ? (
            <div className="card p-8 text-center text-muted text-sm">
              Selecciona una organización para ver sus detalles
            </div>
          ) : (
            <div className="card p-5 flex flex-col gap-4">
              <div>
                <h2 className="text-lg font-medium text-primary">{selected.name}</h2>
                <p className="text-sm text-muted">{selected.slug}</p>
              </div>

              {/* Info */}
              <div className="bg-bg rounded-lg p-3 text-sm flex flex-col gap-1.5">
                <div className="flex justify-between">
                  <span className="text-muted">Estado</span>
                  <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${STATUS_CLASS[selected.subscription_status]}`}>
                    {STATUS_LABEL[selected.subscription_status]}
                  </span>
                </div>
                {selected.trial_ends_at && (
                  <div className="flex justify-between">
                    <span className="text-muted">Trial vence</span>
                    <span className="text-primary">{formatDateLong(selected.trial_ends_at)}</span>
                  </div>
                )}
                {selected.subscribed_at && (
                  <div className="flex justify-between">
                    <span className="text-muted">Activada</span>
                    <span className="text-primary">{formatDate(selected.subscribed_at)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted">Catálogos</span>
                  <span className="text-primary">{selected.catalog_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Cotizaciones</span>
                  <span className="text-primary">{selected.quote_count}</span>
                </div>
              </div>

              {/* Notas */}
              <div>
                <label className="text-sm font-medium text-primary block mb-1">
                  Notas internas
                </label>
                <textarea
                  className="input resize-none text-sm"
                  rows={3}
                  placeholder="Ej: Pagó $250 el 15 ene vía SPEI desde BBVA..."
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                />
              </div>

              {/* Acciones */}
              <div className="flex flex-col gap-2">
                {selected.subscription_status !== 'active' && (
                  <button
                    onClick={() => handleSetStatus(selected.id, 'active')}
                    disabled={saving}
                    className="btn-primary text-sm py-2"
                  >
                    <CheckCircle size={14} />
                    Activar suscripción
                  </button>
                )}
                {selected.subscription_status !== 'trial' && (
                  <button
                    onClick={() => handleSetStatus(selected.id, 'trial')}
                    disabled={saving}
                    className="btn-secondary text-sm py-2"
                  >
                    <Clock size={14} />
                    Regresar a trial
                  </button>
                )}
                {selected.subscription_status !== 'expired' && (
                  <button
                    onClick={() => handleSetStatus(selected.id, 'expired')}
                    disabled={saving}
                    className="btn-danger text-sm py-2"
                  >
                    <XCircle size={14} />
                    Marcar como vencida
                  </button>
                )}
                <button
                  onClick={() => handleToggleActive(selected.id)}
                  disabled={saving}
                  className="btn-secondary text-sm py-2 text-muted"
                >
                  {selected.is_active ? 'Desactivar cuenta' : 'Reactivar cuenta'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
