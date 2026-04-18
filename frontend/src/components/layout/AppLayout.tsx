/*
 * Layout principal — la estructura que rodea todas las páginas internas.
 *
 * Estructura visual:
 *   ┌──────────────────────────────────────────┐
 *   │  Navbar (azul noche)                     │
 *   ├──────────┬───────────────────────────────┤
 *   │ Sidebar  │  <Outlet /> (página actual)   │
 *   │          │                               │
 *   └──────────┴───────────────────────────────┘
 *
 * <Outlet /> es de React Router — renderiza el componente de la
 * ruta hija actual. Si la URL es /quotes, renderiza la página Quotes.
 *
 * useNavigate y useLocation son hooks de React Router:
 *   navigate('/quotes')       → navega programáticamente
 *   location.pathname         → URL actual (para marcar nav item activo)
 */

import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, FileText, BookOpen, LogOut, Wrench,
} from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

interface NavItem {
  icon: typeof LayoutDashboard
  label: string
  path: string
}

const NAV_ITEMS: NavItem[] = [
  { icon: LayoutDashboard, label: 'Dashboard',    path: '/dashboard' },
  { icon: FileText,        label: 'Cotizaciones', path: '/quotes'    },
  { icon: BookOpen,        label: 'Catálogos',    path: '/catalogs'  },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Navbar superior ───────────────────────────── */}
      <header className="bg-primary h-12 flex items-center px-6 flex-shrink-0">
        <div className="flex items-center gap-2 flex-1">
          <Wrench size={16} className="text-accent" />
          <span className="text-white font-medium text-md">
            {user?.organization.name || 'Ferretería SaaS'}
          </span>
        </div>
        <span className="text-white/50 text-sm">
          {user?.full_name}
        </span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Sidebar ───────────────────────────────────── */}
        <aside className="w-52 bg-surface border-r border-border flex flex-col flex-shrink-0">
          <nav className="flex-1 p-3 flex flex-col gap-1 pt-4">
            {NAV_ITEMS.map(({ icon: Icon, label, path }) => {
              const isActive = location.pathname.startsWith(path)
              return (
                <button
                  key={path}
                  onClick={() => navigate(path)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-base
                    transition-colors duration-150 text-left
                    ${isActive
                      ? 'bg-primary text-white font-medium'
                      : 'text-primary hover:bg-bg'
                    }
                  `}
                >
                  <Icon size={15} />
                  {label}
                </button>
              )
            })}
          </nav>

          {/* Botón de logout al fondo del sidebar */}
          <div className="p-3 border-t border-border">
            <button
              onClick={logout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-md
                         text-sm text-muted hover:text-danger hover:bg-danger-light
                         transition-colors duration-150"
            >
              <LogOut size={14} />
              Cerrar sesión
            </button>
          </div>
        </aside>

        {/* ── Contenido principal ───────────────────────── */}
        <main className="flex-1 overflow-auto bg-bg">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
