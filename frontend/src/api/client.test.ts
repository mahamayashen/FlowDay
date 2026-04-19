import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useAuthStore } from '../stores/authStore'
import type { TokenPair } from '../types/auth'

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const newTokens: TokenPair = {
  access_token: 'access-new',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false })
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('apiClient', () => {
  it('attaches Authorization header when tokens exist in store', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ id: '1' }), { status: 200 }),
    )

    await apiClient.get('/auth/me')

    expect(fetchSpy).toHaveBeenCalledOnce()
    const [, init] = fetchSpy.mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get('Authorization')).toBe('Bearer access-abc')
  })

  it('does not attach Authorization header when no tokens in store', async () => {
    const { apiClient } = await import('./client')

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({}), { status: 200 }),
    )

    await apiClient.get('/some/public/endpoint')

    const [, init] = fetchSpy.mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get('Authorization')).toBeNull()
  })

  it('on 401 calls /auth/refresh, updates store, and retries original request', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{}', { status: 401 })) // original fails
      .mockResolvedValueOnce(
        new Response(JSON.stringify(newTokens), { status: 200 }),
      ) // refresh succeeds
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: '1' }), { status: 200 }),
      ) // retry succeeds

    await apiClient.get('/auth/me')

    expect(fetchSpy).toHaveBeenCalledTimes(3)
    // Second call must be to /auth/refresh
    const refreshCall = fetchSpy.mock.calls[1]
    expect(refreshCall[0]).toContain('/auth/refresh')
    // Store must have new tokens
    expect(useAuthStore.getState().tokens?.access_token).toBe('access-new')
  })

  it('on 401 with failed refresh calls logout and does not retry', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout')

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{}', { status: 401 })) // original fails
      .mockResolvedValueOnce(new Response('{}', { status: 401 })) // refresh fails

    await apiClient.get('/auth/me')

    expect(logoutSpy).toHaveBeenCalledOnce()
  })

  it('patch sends PATCH method with serialized body', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ id: '1' }), { status: 200 }),
    )

    await apiClient.patch('/projects/1', { name: 'Updated' })

    const [url, init] = fetchSpy.mock.calls[0]
    expect(url).toBe('/projects/1')
    expect(init?.method).toBe('PATCH')
    expect(init?.body).toBe(JSON.stringify({ name: 'Updated' }))
  })

  it('patch attaches Authorization header', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 200 }),
    )

    await apiClient.patch('/projects/1', { name: 'X' })

    const [, init] = fetchSpy.mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get('Authorization')).toBe('Bearer access-abc')
  })

  it('patch retries with new token after 401', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{}', { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(newTokens), { status: 200 }))
      .mockResolvedValueOnce(new Response('{}', { status: 200 }))

    await apiClient.patch('/projects/1', { name: 'X' })

    expect(fetchSpy).toHaveBeenCalledTimes(3)
    expect(useAuthStore.getState().tokens?.access_token).toBe('access-new')
  })

  it('delete sends DELETE method with no body', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(null, { status: 204 }),
    )

    await apiClient.delete('/projects/1')

    const [url, init] = fetchSpy.mock.calls[0]
    expect(url).toBe('/projects/1')
    expect(init?.method).toBe('DELETE')
    expect(init?.body).toBeUndefined()
  })

  it('delete attaches Authorization header', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(null, { status: 204 }),
    )

    await apiClient.delete('/projects/1')

    const [, init] = fetchSpy.mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get('Authorization')).toBe('Bearer access-abc')
  })

  it('delete retries with new token after 401', async () => {
    const { apiClient } = await import('./client')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{}', { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(newTokens), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))

    await apiClient.delete('/projects/1')

    expect(fetchSpy).toHaveBeenCalledTimes(3)
    expect(useAuthStore.getState().tokens?.access_token).toBe('access-new')
  })
})
