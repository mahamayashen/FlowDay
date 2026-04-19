import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useAuthStore } from '../stores/authStore'
import type { TokenPair } from '../types/auth'
import type { Project } from '../types/project'

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockProjects: Project[] = [
  {
    id: 'proj-1',
    user_id: 'user-1',
    name: 'Alpha',
    color: '#f59e0b',
    client_name: null,
    hourly_rate: null,
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'proj-2',
    user_id: 'user-1',
    name: 'Beta',
    color: '#3b82f6',
    client_name: 'Acme',
    hourly_rate: '100.00',
    status: 'active',
    created_at: '2026-01-02T00:00:00Z',
  },
]

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false })
  vi.restoreAllMocks()
})

describe('useProjects', () => {
  it('returns projects list from API', async () => {
    const { useProjects } = await import('./projects')
    useAuthStore.getState().setTokens(mockTokens)

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockProjects), { status: 200 }),
    )

    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[0].name).toBe('Alpha')
    expect(result.current.data?.[1].name).toBe('Beta')
  })

  it('shows loading state before resolution', async () => {
    const { useProjects } = await import('./projects')
    useAuthStore.getState().setTokens(mockTokens)

    vi.spyOn(globalThis, 'fetch').mockImplementation(
      () => new Promise(() => {}), // never resolves
    )

    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() })

    expect(result.current.isLoading).toBe(true)
  })

  it('exposes error when fetch fails', async () => {
    const { useProjects } = await import('./projects')
    useAuthStore.getState().setTokens(mockTokens)

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response('{}', { status: 500 }),
    )

    const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
