import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import ProtectedRoute from './ProtectedRoute'
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

function renderProtected(initialPath = '/dashboard'): void {
  render(
    <MemoryRouter initialEntries={[initialPath]} future={future}>
      <Routes>
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <div data-testid="protected-content" />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div data-testid="page-login" />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isUserLoading: false,
  })
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ProtectedRoute', () => {
  it('redirects to /login when not authenticated', () => {
    renderProtected()
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    useAuthStore.setState({ user: mockUser, tokens: mockTokens, isAuthenticated: true })
    renderProtected()
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.queryByTestId('page-login')).not.toBeInTheDocument()
  })

  it('fetches /auth/me when tokens exist but user is null', async () => {
    useAuthStore.setState({ user: null, tokens: mockTokens, isAuthenticated: true })

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockUser), { status: 200 }),
    )

    renderProtected()

    await waitFor(() =>
      expect(useAuthStore.getState().user).toEqual(mockUser),
    )
    expect(fetchSpy).toHaveBeenCalledOnce()
    expect(fetchSpy.mock.calls[0][0]).toContain('/auth/me')
  })

  it('shows loading state instead of children when tokens exist but user is null', () => {
    useAuthStore.setState({ user: null, tokens: mockTokens, isAuthenticated: true })
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {})) // never resolves
    renderProtected()
    expect(screen.getByTestId('auth-loading')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('logs out and redirects when /auth/me fetch fails', async () => {
    useAuthStore.setState({ user: null, tokens: mockTokens, isAuthenticated: true })

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('{}', { status: 401 })) // /auth/me
      .mockResolvedValueOnce(new Response('{}', { status: 401 })) // /auth/refresh

    renderProtected()

    await waitFor(() =>
      expect(screen.getByTestId('page-login')).toBeInTheDocument(),
    )
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('shows error message and keeps session when /auth/me returns 5xx', async () => {
    useAuthStore.setState({ user: null, tokens: mockTokens, isAuthenticated: true })

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 503 }),
    )

    renderProtected()

    await waitFor(() =>
      expect(screen.getByTestId('auth-error')).toBeInTheDocument(),
    )
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().tokens).toEqual(mockTokens)
  })
})
