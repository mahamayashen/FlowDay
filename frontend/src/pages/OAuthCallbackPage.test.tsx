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

function renderCallback(provider: string, code: string): void {
  render(
    <MemoryRouter
      initialEntries={[`/auth/${provider}/callback?code=${code}`]}
      future={future}
    >
      <Routes>
        <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />
        <Route path="/dashboard" element={<div data-testid="page-dashboard" />} />
        <Route path="/login" element={<div data-testid="page-login" />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false })
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('OAuthCallbackPage', () => {
  it('shows loading state while exchanging code', () => {
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {})) // never resolves
    renderCallback('google', 'code-123')
    expect(screen.getByTestId('oauth-loading')).toBeInTheDocument()
  })

  it('calls the backend callback endpoint with the code for google', async () => {
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockTokens), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), { status: 200 }),
      )

    renderCallback('google', 'code-abc')

    await waitFor(() =>
      expect(fetchSpy.mock.calls[0][0]).toContain('/auth/google/callback'),
    )
    expect(new URL(fetchSpy.mock.calls[0][0] as string, 'http://x').searchParams.get('code')).toBe(
      'code-abc',
    )
  })

  it('stores tokens and user in authStore on success', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockTokens), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), { status: 200 }),
      )

    renderCallback('google', 'code-abc')

    await waitFor(() => expect(useAuthStore.getState().isAuthenticated).toBe(true))
    expect(useAuthStore.getState().tokens).toEqual(mockTokens)
    expect(useAuthStore.getState().user).toEqual(mockUser)
  })

  it('navigates to /dashboard on success', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockTokens), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(mockUser), { status: 200 }),
      )

    renderCallback('google', 'code-abc')

    await waitFor(() =>
      expect(screen.getByTestId('page-dashboard')).toBeInTheDocument(),
    )
  })

  it('shows an error message when code exchange fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Invalid code' }), { status: 401 }),
    )

    renderCallback('google', 'bad-code')

    await waitFor(() =>
      expect(screen.getByTestId('oauth-error')).toBeInTheDocument(),
    )
  })

  it('shows a back-to-login link on error', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 500 }),
    )

    renderCallback('github', 'bad-code')

    await waitFor(() =>
      expect(screen.getByTestId('link-back-to-login')).toBeInTheDocument(),
    )
  })
})
