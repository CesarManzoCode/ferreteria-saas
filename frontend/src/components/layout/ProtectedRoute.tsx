/*
 * ProtectedRoute — guarda de rutas privadas.
 *
 * Si el usuario no está logueado, redirige a /login.
 * Si está logueado, renderiza el contenido normalmente.
 *
 * Uso en App.tsx:
 *   <Route element={<ProtectedRoute />}>
 *     <Route path="/dashboard" element={<Dashboard />} />
 *   </Route>
 *
 * Mientras verifica si hay sesión (isLoading), muestra un spinner
 * para evitar un flash de la página de login antes de redirigir.
 */

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { PageSpinner } from '../ui'

export default function ProtectedRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) return <PageSpinner />
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}
