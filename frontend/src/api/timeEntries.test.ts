import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useActiveTimer } from './timeEntries'
import type { TimeEntry } from '../types/timeEntry'

// Mock apiClient
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { apiClient } from './client'

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

const stoppedEntry: TimeEntry = {
  id: 'entry-stopped',
  task_id: 'task-1',
  started_at: '2026-04-19T10:00:00Z',
  ended_at: '2026-04-19T10:30:00Z',
  duration_seconds: 1800,
  created_at: '2026-04-19T10:00:00Z',
}

const activeEntry: TimeEntry = {
  id: 'entry-active',
  task_id: 'task-2',
  started_at: '2026-04-19T11:00:00Z',
  ended_at: null,
  duration_seconds: null,
  created_at: '2026-04-19T11:00:00Z',
}

describe('useActiveTimer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns the entry with ended_at === null from GET /time-entries', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      ok: true,
      json: async () => [stoppedEntry, activeEntry],
    } as Response)

    const { result } = renderHook(() => useActiveTimer(), { wrapper })

    await waitFor(() => expect(result.current.data).toBeDefined())

    expect(result.current.data).toEqual(activeEntry)
  })

  it('returns undefined when all entries are stopped', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      ok: true,
      json: async () => [stoppedEntry],
    } as Response)

    const { result } = renderHook(() => useActiveTimer(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toBeUndefined()
  })
})
