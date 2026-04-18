/*
 * Página de Login.
 *
 * Estado local del formulario con useState — no necesitamos
 * una librería de forms para algo tan simple.
 *
 * Flujo:
 *   1. Usuario llena email + password
 *   2. Submit → llama a login() de la API
 *   3. Si OK → guarda sesión → navega a /dashboard
 *   4. Si error → muestra mensaje con react-hot-toast
 */

import { useState, type FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Wrench } from 'lucide-react'
import toast from 'react-hot-toast'
import { login as loginApi } from '../api/auth'
import { useAuth } from '../hooks/useAuth'
import { Button, Input } from '../components/ui'
import { getErrorMessage } from '../api/client'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await loginApi({ email, password })
      login(response)
      navigate('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="card w-full max-w-sm p-8">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <Wrench size={16} className="text-accent" />
          </div>
          <span className="text-xl font-medium text-primary">Ferretería SaaS</span>
        </div>

        <h1 className="text-2xl font-medium text-primary mb-1">Iniciar sesión</h1>
        <p className="text-base text-muted mb-6">Ingresa a tu cuenta</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="Correo electrónico"
            type="email"
            placeholder="tu@correo.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            autoFocus
          />
          <Input
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          <Button type="submit" loading={loading} className="mt-2 w-full">
            Entrar
          </Button>
        </form>

        <p className="text-sm text-muted text-center mt-6">
          ¿No tienes cuenta?{' '}
          <Link to="/register" className="text-accent hover:underline font-medium">
            Registra tu ferretería
          </Link>
        </p>
      </div>
    </div>
  )
}

/* ── RegisterPage ─────────────────────────────────────────── */

import { register as registerApi } from '../api/auth'

export function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    organization_name: '',
  })

  function handleChange(field: string, value: string) {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (form.password.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres')
      return
    }
    setLoading(true)
    try {
      const response = await registerApi(form)
      login(response)
      navigate('/dashboard')
      toast.success('¡Bienvenido! Tu cuenta está lista.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="card w-full max-w-sm p-8">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <Wrench size={16} className="text-accent" />
          </div>
          <span className="text-xl font-medium text-primary">Ferretería SaaS</span>
        </div>

        <h1 className="text-2xl font-medium text-primary mb-1">Crea tu cuenta</h1>
        <p className="text-base text-muted mb-6">Registra tu ferretería gratis</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="Nombre de tu ferretería"
            placeholder="Ferretería García"
            value={form.organization_name}
            onChange={e => handleChange('organization_name', e.target.value)}
            required
            autoFocus
          />
          <Input
            label="Tu nombre completo"
            placeholder="Juan García"
            value={form.full_name}
            onChange={e => handleChange('full_name', e.target.value)}
            required
          />
          <Input
            label="Correo electrónico"
            type="email"
            placeholder="tu@correo.com"
            value={form.email}
            onChange={e => handleChange('email', e.target.value)}
            required
          />
          <Input
            label="Contraseña"
            type="password"
            placeholder="Mínimo 8 caracteres"
            value={form.password}
            onChange={e => handleChange('password', e.target.value)}
            required
          />
          <Button type="submit" loading={loading} className="mt-2 w-full">
            Crear cuenta
          </Button>
        </form>

        <p className="text-sm text-muted text-center mt-6">
          ¿Ya tienes cuenta?{' '}
          <Link to="/login" className="text-accent hover:underline font-medium">
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  )
}
