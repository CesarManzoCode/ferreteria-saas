/*
 * Utilidades puras — funciones sin estado ni efectos secundarios.
 * Se pueden testear de forma aislada y reutilizar en cualquier parte.
 */

/* Formatea un número como precio en MXN: $1,500.00 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
  }).format(amount)
}

/* Formatea una fecha ISO como: 15 ene 2025 */
export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

/* Formatea una fecha ISO como: 15 de enero de 2025 */
export function formatDateLong(isoString: string): string {
  return new Date(isoString).toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

/* Labels legibles para estados de cotización */
export const QUOTE_STATUS_LABELS: Record<string, string> = {
  draft:    'Borrador',
  sent:     'Enviada',
  accepted: 'Aceptada',
  expired:  'Vencida',
}

/* Color del badge según estado */
export const QUOTE_STATUS_CLASS: Record<string, string> = {
  draft:    'badge-draft',
  sent:     'badge-sent',
  accepted: 'badge-accepted',
  expired:  'badge-expired',
}

/* Color del badge de score fuzzy */
export function scoreColor(score: number): string {
  if (score >= 80) return 'bg-success-light text-success'
  if (score >= 60) return 'bg-warning-light text-warning'
  return 'bg-bg text-muted'
}

/* Trunca un string largo con ellipsis */
export function truncate(str: string, max = 40): string {
  return str.length > max ? str.slice(0, max) + '…' : str
}
