import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useAuthStore } from '../stores/authStore'
import type { TokenPair } from '../types/auth'
import type { Task } from '../types/task'

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockTasks: Task[] = [
  {
    id: 'task-1',
    project_id: 'proj-1',
    title: 'First task',
    description: null,
    estimate_minutes: 30,
    priority: 'medium',
    status: 'todo',
    due_date: null,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: null,
  },
  {
    id: 'task-2',
    project_id: 'proj-1',
    title: 'Second task',
    description: 'Some details',
    estimate_minutes: 60,
    priority: 'high',
    status: 'in_progress',
    due_date: '2026-05-01',
    created_at: '2026-01-02T00:00:00Z',
    completed_at: null,
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

describe('useProjectTasks', () => {
  it('returns tasks list for a project', async () => {
    const { useProjectTasks } = await import('./tasks')
    useAuthStore.getState().setTokens(mockTokens)

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockTasks), { status: 200 }),
    )

    const { result } = renderHook(() => useProjectTasks('proj-1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[0].title).toBe('First task')
    expect(result.current.data?.[1].title).toBe('Second task')
  })

  it('shows loading state before resolution', async () => {
    const { useProjectTasks } = await import('./tasks')
    useAuthStore.getState().setTokens(mockTokens)

    vi.spyOn(globalThis, 'fetch').mockImplementation(
      () => new Promise(() => {}),
    )

    const { result } = renderHook(() => useProjectTasks('proj-1'), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })

  it('fetches from the correct nested URL', async () => {
    const { useProjectTasks } = await import('./tasks')
    useAuthStore.getState().setTokens(mockTokens)

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockTasks), { status: 200 }),
    )

    const { result } = renderHook(() => useProjectTasks('proj-42'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(fetchSpy.mock.calls[0][0]).toBe('/projects/proj-42/tasks')
  })
})
