/*
 * Pantalla que aparece cuando el trial venció o la cuenta está expirada.
 * El usuario puede seguir viendo esta pantalla pero no acceder al sistema.
 * Le indica cómo contactar para pagar y reactivar.
 */

import { useAuth } from '../hooks/useAuth'
import { Wrench, Mail, MessageCircle } from 'lucide-react'
import { Button } from '../components/ui'

export default function SubscriptionExpiredPage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <Wrench size={16} className="text-accent" />
          </div>
          <span className="text-xl font-medium text-primary">Ferretería SaaS</span>
        </div>

        <div className="card p-8 text-center">
          {/* Ícono */}
          <div className="w-14 h-14 bg-warning-light rounded-full flex items-center justify-center mx-auto mb-5">
            <span className="text-2xl">⏰</span>
          </div>

          <h1 className="text-2xl font-medium text-primary mb-2">
            Tu período de prueba terminó
          </h1>
          <p className="text-base text-muted mb-6">
            {user?.organization.name} completó sus 14 días de prueba gratuita.
            Para seguir usando el sistema contáctanos para activar tu cuenta.
          </p>

          {/* Plan */}
          <div className="bg-bg border border-border rounded-lg p-4 mb-6 text-left">
            <div className="flex items-center justify-between mb-2">
              <span className="text-base font-medium text-primary">Plan mensual</span>
              <span className="text-2xl font-medium text-primary">$250 <span className="text-sm text-muted font-normal">MXN/mes</span></span>
            </div>
            <ul className="text-sm text-muted space-y-1">
              <li>✓ Catálogos ilimitados</li>
              <li>✓ Búsqueda fuzzy inteligente</li>
              <li>✓ Cotizaciones en PDF ilimitadas</li>
              <li>✓ Soporte por WhatsApp</li>
            </ul>
          </div>

          {/* Contacto */}
          <p className="text-sm text-muted mb-4">
            Escríbenos para activar tu cuenta. Aceptamos transferencia bancaria.
          </p>

          <div className="flex flex-col gap-3">
            <a
              href="https://wa.me/523312345678?text=Hola,%20quiero%20activar%20mi%20cuenta%20de%20Ferretería%20SaaS"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary w-full"
            >
              <MessageCircle size={15} />
              Contactar por WhatsApp
            </a>
            <a
              href="mailto:hola@tudominio.com?subject=Activar cuenta Ferretería SaaS"
              className="btn-secondary w-full"
            >
              <Mail size={15} />
              Enviar correo
            </a>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full text-center text-sm text-muted hover:text-primary mt-4 transition-colors"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}
