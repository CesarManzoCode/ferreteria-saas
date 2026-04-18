/*
 * Contexto de autenticación — estado global del usuario.
 *
 * ¿Qué es un Context en React?
 *   Es una forma de pasar datos a cualquier componente en el árbol
 *   sin tener que pasarlos manualmente como props por cada nivel.
 *
 *   Sin Context:
 *     App → Layout → Sidebar → UserMenu (props en cada nivel)
 *   Con Context:
 *     UserMenu → useAuth() → obtiene el usuario directamente
 *
 * AuthProvider envuelve toda la app y provee:
 *   user      → el usuario actual (null si no está logueado)
 *   isLoading → true mientras verifica si hay sesión guardada
 *   login()   → guarda token y usuario
 *   logout()  → limpia sesión y redirige
 *
 * useAuth() es el hook que usan los componentes para acceder al contexto.
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { clearSession, getStoredUser, saveSession } from '../api/auth'
import type { TokenResponse, User } from '../types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (response: TokenResponse) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  /*
   * Al montar el provider, verificamos si hay un usuario guardado
   * en localStorage. Esto permite que si el usuario cierra y abre
   * el browser, no tenga que volver a hacer login.
   *
   * No hacemos fetch al backend aquí para verificar el token —
   * lo verificará el primer request que haga al backend.
   * Si el token expiró, el interceptor de axios captura el 401
   * y llama a logout() automáticamente.
   */
  useEffect(() => {
    const stored = getStoredUser()
    if (stored) setUser(stored)
    setIsLoading(false)
  }, [])

  function login(response: TokenResponse) {
    saveSession(response)
    setUser(response.user)
  }

  function logout() {
    clearSession()
    setUser(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

/* Hook para usar el contexto — lanza error si se usa fuera del provider */
export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
