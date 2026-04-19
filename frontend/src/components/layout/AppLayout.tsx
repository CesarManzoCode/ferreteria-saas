import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, FileText, BookOpen, LogOut, Wrench, ShieldCheck } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

interface NavItem {
  icon: typeof LayoutDashboard
  label: string
  path: string
  adminOnly?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { icon: LayoutDashboard, label: 'Dashboard',    path: '/dashboard' },
  { icon: FileText,        label: 'Cotizaciones', path: '/quotes'    },
  { icon: BookOpen,        label: 'Catálogos',    path: '/catalogs'  },
  { icon: ShieldCheck,     label: 'Admin',        path: '/admin', adminOnly: true },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Navbar ── */}
      <header className="bg-primary h-12 flex items-center px-6 flex-shrink-0 gap-4">
        <div className="flex items-center gap-2 flex-1">
          <Wrench size={16} className="text-accent" />
          <span className="text-white font-medium text-md">
            {user?.organization.name || 'Ferretería SaaS'}
          </span>
        </div>
        <span className="text-white/50 text-sm hidden sm:block">
          {user?.full_name}
        </span>
        <button
          onClick={logout}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm
                     text-white/70 hover:text-white hover:bg-white/10
                     transition-colors duration-150"
        >
          <LogOut size={14} />
          Cerrar sesión
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Sidebar ── */}
        <aside className="w-52 bg-surface border-r border-border flex flex-col flex-shrink-0">
          <nav className="flex-1 p-3 flex flex-col gap-1 pt-4">
            {NAV_ITEMS
              .filter(item => !item.adminOnly || user?.role === 'admin')
              .map(({ icon: Icon, label, path }) => {
                const isActive = location.pathname.startsWith(path)
                return (
                  <button
                    key={path}
                    onClick={() => navigate(path)}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-base
                      transition-colors duration-150 text-left
                      ${isActive ? 'bg-primary text-white font-medium' : 'text-primary hover:bg-bg'}
                    `}
                  >
                    <Icon size={15} />
                    {label}
                  </button>
                )
              })}
          </nav>
        </aside>

        {/* ── Contenido ── */}
        <main className="flex-1 overflow-auto bg-bg">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
