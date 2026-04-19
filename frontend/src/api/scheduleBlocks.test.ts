import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useAuthStore } from '../stores/authStore'
import type { TokenPair } from '../types/auth'
import type { ScheduleBlock } from '../types/scheduleBlock'
import { useScheduleBlocks } from './scheduleBlocks'

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockBlocks: ScheduleBlock[] = [
  {
    id: 'block-1',
    task_id: 'task-1',
    date: '2026-04-18',
    start_hour: 9,
    end_hour: 10,
    source: 'manual',
    created_at: '2026-04-18T09:00:00Z',
  },
  {
    id: 'block-2',
    task_id: 'task-2',
    date: '2026-04-18',
    start_hour: 14,
    end_hour: 15.5,
    source: 'google_calendar',
    created_at: '2026-04-18T14:00:00Z',
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
  useAuthStore.getState().setTokens(mockTokens)
  vi.restoreAllMocks()
})

describe('useScheduleBlocks', () => {
  it('fetches blocks from correct URL with date query param', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockBlocks), { status: 200 }),
    )

    const { result } = renderHook(() => useScheduleBlocks('2026-04-18'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(fetchSpy).toHaveBeenCalledWith(
      '/schedule-blocks?date=2026-04-18',
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('returns block data on success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockBlocks), { status: 200 }),
    )

    const { result } = renderHook(() => useScheduleBlocks('2026-04-18'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[0].id).toBe('block-1')
  })

  it('shows loading state before resolution', () => {
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(() => {}))

    const { result } = renderHook(() => useScheduleBlocks('2026-04-18'), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)
  })

  it('is disabled when date is empty string', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')

    const { result } = renderHook(() => useScheduleBlocks(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(false)
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})
