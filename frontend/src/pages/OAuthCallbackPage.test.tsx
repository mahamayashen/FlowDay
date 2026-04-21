import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import OAuthCallbackPage from './OAuthCallbackPage'
import { useAuthStore } from '../stores/authStore'
import type { TokenPair, User } from '../types/auth'

const future = { v7_startTransition: true, v7_relativeSplatPath: true } as const

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockUser: User = {
  id: 'usr-1',
  email: 'alice@example.com',
  name: 'Alice',
  settings_json: {},
  created_at: '2026-01-01T00:00:00Z',
}

function renderCallback(provider: string, code: string, state?: string): void {
  const search = state
    ? `?code=${code}&state=${state}`
    : `?code=${code}`
  render(
    <MemoryRouter
      initialEntries={[`/auth/${provider}/callback${search}`]}
      future={future}
    >
      <Routes>
        <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />
        <Route path="/" element={<div data-testid="page-home" />} />
        <Route path="/login" element={<div data-testid="page-login" />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false })
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('OAuthCallbackPage', () => {
  it('shows loading state while exchanging code', () => {
    sessionStorage.setItem('oauth_state', 'state-token')
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {})) // never resolves
    renderCallback('google', 'code-123', 'state-token')
    expect(screen.getByTestId('oauth-loading')).toBeInTheDocument()
  })

  it('calls the backend callback endpoint with the code for google', async () => {
    sessionStorage.setItem('oauth_state', 'state-token')
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockTokens), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), { status: 200 }),
      )

    renderCallback('google', 'code-abc', 'state-token')

    await waitFor(() =>
      expect(fetchSpy.mock.calls[0][0]).toContain('/auth/google/callback'),
    )
    const requestInit = fetchSpy.mock.calls[0][1] as RequestInit
    expect(requestInit.method).toBe('POST')
    expect(JSON.parse(requestInit.body as string)).toEqual({ code: 'code-abc' })
  })

  it('stores tokens and user in authStore on success', async () => {
    sessionStorage.setItem('oauth_state', 'state-token')
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockTokens), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), { status: 200 }),
      )

    renderCallback('google', 'code-abc', 'state-token')

    await waitFor(() => expect(useAuthStore.getState().isAuthenticated).toBe(true))
    expect(useAuthStore.getState().tokens).toEqual(mockTokens)
    expect(useAuthStore.getState().user).toEqual(mockUser)
  })

  it('navigates to / (home) on success', async () => {
    sessionStorage.setItem('oauth_state', 'state-token')
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockTokens), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), { status: 200 }),
      )

    renderCallback('google', 'code-abc', 'state-token')

    await waitFor(() =>
      expect(screen.getByTestId('page-home')).toBeInTheDocument(),
    )
  })

  it('shows an error message when code exchange fails', async () => {
    sessionStorage.setItem('oauth_state', 'state-token')
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Invalid code' }), { status: 401 }),
    )

    renderCallback('google', 'bad-code', 'state-token')

    await waitFor(() =>
      expect(screen.getByTestId('oauth-error')).toBeInTheDocument(),
    )
  })

  it('shows a back-to-login link on error', async () => {
    sessionStorage.setItem('oauth_state', 'state-token')
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 500 }),
    )

    renderCallback('github', 'bad-code', 'state-token')

    await waitFor(() =>
      expect(screen.getByTestId('link-back-to-login')).toBeInTheDocument(),
    )
  })

  it('shows an error when state param is missing from callback URL', async () => {
    sessionStorage.setItem('oauth_state', 'expected-state')
    // mock fetch to succeed so the test validates state, not network
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(mockTokens), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(mockUser), { status: 200 }))
    // no state in URL
    renderCallback('google', 'code-abc')

    await waitFor(() =>
      expect(screen.getByTestId('oauth-error')).toBeInTheDocument(),
    )
  })

  it('shows an error when state param does not match sessionStorage', async () => {
    sessionStorage.setItem('oauth_state', 'expected-state')
    // mock fetch to succeed so the test validates state, not network
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(mockTokens), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(mockUser), { status: 200 }))
    renderCallback('google', 'code-abc', 'wrong-state')

    await waitFor(() =>
      expect(screen.getByTestId('oauth-error')).toBeInTheDocument(),
    )
  })

  it('clears oauth_state from sessionStorage after successful validation', async () => {
    const state = 'valid-state-token'
    sessionStorage.setItem('oauth_state', state)
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(mockTokens), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(mockUser), { status: 200 }))

    renderCallback('google', 'code-abc', state)

    await waitFor(() =>
      expect(screen.getByTestId('page-home')).toBeInTheDocument(),
    )
    expect(sessionStorage.getItem('oauth_state')).toBeNull()
  })
})
