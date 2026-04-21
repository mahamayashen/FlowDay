import { apiClient, buildUrl } from './client'
import type { TokenPair, User } from '../types/auth'

export async function exchangeOAuthCode(
  provider: 'google' | 'github',
  code: string,
  signal?: AbortSignal,
): Promise<TokenPair> {
  const url = `/auth/${provider}/callback`
  const res = await fetch(buildUrl(url), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
    signal,
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as { detail?: string }).detail ?? 'OAuth exchange failed')
  }
  return res.json() as Promise<TokenPair>
}

export class AuthError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'AuthError'
  }
}

export async function fetchCurrentUser(signal?: AbortSignal): Promise<User> {
  const res = await apiClient.get('/auth/me', signal)
  if (!res.ok) {
    throw new AuthError('Failed to fetch current user', res.status)
  }
  return res.json() as Promise<User>
}

