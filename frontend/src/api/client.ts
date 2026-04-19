/*
 * Cliente HTTP centralizado para comunicarse con el backend.
 *
 * ¿Por qué no usar fetch() directamente en cada componente?
 *   Porque cada llamada necesitaría:
 *     1. Construir la URL completa con la base
 *     2. Agregar el header Authorization: Bearer <token>
 *     3. Parsear el JSON de la respuesta
 *     4. Manejar errores HTTP (401, 404, 422...)
 *
 *   Al centralizar esto, cada función de API se ve así:
 *     const catalogs = await api.get('/catalogs')
 *   En lugar de 15 líneas de boilerplate.
 *
 * ¿Por qué axios y no fetch nativo?
 *   axios tiene mejor manejo de errores por defecto — lanza
 *   excepciones en respuestas 4xx/5xx en lugar de retornar
 *   una Response que tienes que chequear manualmente.
 *   También serializa/deserializa JSON automáticamente.
 */

import axios, { AxiosError } from 'axios'

// URL base del backend — en desarrollo apunta a localhost
// En producción, Vite reemplaza esta variable con el valor del .env
const BASE_URL = ''

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/*
 * Interceptor de request — se ejecuta ANTES de cada llamada.
 * Lee el token del localStorage y lo agrega al header.
 *
 * ¿Por qué localStorage y no cookies?
 *   Para el MVP, localStorage es más simple. Cookies tienen ventajas
 *   de seguridad (httpOnly previene XSS), pero requieren configuración
 *   adicional en el backend. Para un MVP que se valida primero, 
 *   localStorage está bien.
 */
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/*
 * Interceptor de response — se ejecuta DESPUÉS de cada llamada.
 * Si el backend retorna 401 (token expirado o inválido),
 * limpia el token y redirige al login automáticamente.
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    // Suscripción vencida — redirigir a pantalla de expiración
    if (error.response?.status === 403) {
      const data = error.response.data as { detail?: string }
      if (data?.detail === 'subscription_expired') {
        if (!window.location.pathname.includes('/expired')) {
          window.location.href = '/expired'
        }
      }
    }
    return Promise.reject(error)
  }
)

/*
 * Extrae el mensaje de error de una respuesta de la API.
 * FastAPI puede retornar:
 *   { detail: "string simple" }
 *   { detail: [{ msg: "error de validación" }] }
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail.map((e: { msg: string }) => e.msg).join(', ')
    }
  }
  return 'Ocurrió un error inesperado'
}
