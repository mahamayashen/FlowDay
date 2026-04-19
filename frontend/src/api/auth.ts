import { apiClient } from './client'
import type { TokenPair, User } from '../types/auth'

export async function exchangeOAuthCode(
  provider: 'google' | 'github',
  code: string,
  signal?: AbortSignal,
): Promise<TokenPair> {
  const url = `/auth/${provider}/callback?code=${encodeURIComponent(code)}`
  const res = await fetch(url, { signal })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as { detail?: string }).detail ?? 'OAuth exchange failed')
  }
  return res.json() as Promise<TokenPair>
}

export async function fetchCurrentUser(signal?: AbortSignal): Promise<User> {
  const res = await apiClient.get('/auth/me', signal)
  if (!res.ok) {
    throw new Error('Failed to fetch current user')
  }
  return res.json() as Promise<User>
}

export async function refreshTokens(refreshToken: string): Promise<TokenPair> {
  const res = await fetch('/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!res.ok) {
    throw new Error('Token refresh failed')
  }
  return res.json() as Promise<TokenPair>
}
