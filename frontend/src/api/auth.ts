/*
 * Funciones de API para autenticación.
 * Cada función corresponde a un endpoint del backend.
 * Retornan los datos directamente — el manejo de errores
 * queda en el componente que las llama.
 */

import { apiClient } from './client'
import type { TokenResponse, User } from '../types'

export interface RegisterPayload {
  full_name: string
  email: string
  password: string
  organization_name: string
}

export interface LoginPayload {
  email: string
  password: string
}

export async function register(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/register', payload)
  return data
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', payload)
  return data
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>('/api/v1/auth/me')
  return data
}

/* Guarda el token y datos de usuario en localStorage */
export function saveSession(response: TokenResponse): void {
  localStorage.setItem('access_token', response.access_token)
  localStorage.setItem('user', JSON.stringify(response.user))
}

/* Lee el usuario del localStorage sin hacer fetch */
export function getStoredUser(): User | null {
  const raw = localStorage.getItem('user')
  if (!raw) return null
  try { return JSON.parse(raw) as User }
  catch { return null }
}

export function clearSession(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}
