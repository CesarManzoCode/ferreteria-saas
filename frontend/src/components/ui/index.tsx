/*
 * Componentes UI reutilizables del sistema de diseño.
 *
 * Todos los componentes usan las clases definidas en index.css
 * y los tokens de tailwind.config.js — nunca colores hardcodeados.
 *
 * Cada componente acepta `className` para extensión puntual
 * sin romper el diseño base.
 */

import { ReactNode, ButtonHTMLAttributes, InputHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'

/* ── Button ──────────────────────────────────────────────── */

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger'
  loading?: boolean
  children: ReactNode
}

export function Button({
  variant = 'primary',
  loading = false,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const base = variant === 'primary'   ? 'btn-primary'
             : variant === 'secondary' ? 'btn-secondary'
             :                           'btn-danger'

  return (
    <button
      className={`${base} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 size={14} className="animate-spin" />}
      {children}
    </button>
  )
}

/* ── Input ───────────────────────────────────────────────── */

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-primary">{label}</label>
      )}
      <input
        className={`input ${error ? 'border-danger focus:border-danger focus:ring-danger/20' : ''} ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  )
}

/* ── Textarea ────────────────────────────────────────────── */

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export function Textarea({ label, error, className = '', ...props }: TextareaProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-primary">{label}</label>
      )}
      <textarea
        className={`input resize-none ${error ? 'border-danger' : ''} ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  )
}

/* ── Badge ───────────────────────────────────────────────── */

interface BadgeProps {
  status: string
  label: string
}

export function Badge({ status, label }: BadgeProps) {
  const classes: Record<string, string> = {
    draft:    'badge badge-draft',
    sent:     'badge badge-sent',
    accepted: 'badge badge-accepted',
    expired:  'badge badge-expired',
  }
  return (
    <span className={classes[status] || 'badge badge-draft'}>
      {label}
    </span>
  )
}

/* ── Spinner ─────────────────────────────────────────────── */

export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <div className="flex items-center justify-center">
      <Loader2 size={size} className="animate-spin text-muted" />
    </div>
  )
}

/* ── PageSpinner — pantalla completa de carga ────────────── */

export function PageSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <Spinner size={32} />
    </div>
  )
}

/* ── EmptyState ──────────────────────────────────────────── */

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      {icon && <div className="text-muted mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-primary mb-2">{title}</h3>
      {description && <p className="text-base text-muted mb-6 max-w-sm">{description}</p>}
      {action}
    </div>
  )
}

/* ── Card ────────────────────────────────────────────────── */

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`}>{children}</div>
}

/* ── Divider ─────────────────────────────────────────────── */

export function Divider() {
  return <hr className="border-border" />
}

/* ── ScoreBadge — para resultados de búsqueda ───────────── */

export function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? 'bg-success-light text-success'
              : score >= 60 ? 'bg-warning-light text-warning'
              : 'bg-bg text-muted border border-border'
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${color}`}>
      {Math.round(score)}
    </span>
  )
}
