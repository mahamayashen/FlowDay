import { useAuthStore } from '../stores/authStore'
import type { TokenPair } from '../types/auth'

let refreshPromise: Promise<TokenPair | null> | null = null

async function attemptRefresh(): Promise<TokenPair | null> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const tokens = useAuthStore.getState().tokens
    if (!tokens) return null

    const res = await fetch('/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    })

    if (!res.ok) {
      useAuthStore.getState().logout()
      return null
    }

    const newTokens: TokenPair = await res.json()
    useAuthStore.getState().setTokens(newTokens)
    return newTokens
  })().finally(() => {
    refreshPromise = null
  })

  return refreshPromise
}

async function request(
  method: string,
  url: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<Response> {
  const tokens = useAuthStore.getState().tokens

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (tokens) {
    headers['Authorization'] = `Bearer ${tokens.access_token}`
  }

  const init: RequestInit = { method, headers, signal }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  const res = await fetch(url, init)

  if (res.status === 401 && tokens) {
    const newTokens = await attemptRefresh()
    if (!newTokens) return res

    // Retry with new access token
    return fetch(url, {
      ...init,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${newTokens.access_token}` },
    })
  }

  return res
}

export const apiClient = {
  get: (url: string, signal?: AbortSignal): Promise<Response> => request('GET', url, undefined, signal),
  post: (url: string, body?: unknown, signal?: AbortSignal): Promise<Response> => request('POST', url, body, signal),
}
