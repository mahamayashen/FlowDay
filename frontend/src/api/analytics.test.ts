import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

import { apiClient } from './client'
import type { PlannedVsActualResponse, WeeklyStatsResponse } from '../types/analytics'

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockDailyResponse: PlannedVsActualResponse = {
  date: '2025-01-15',
  tasks: [
    {
      task_id: 'task-1',
      task_title: 'Write tests',
      planned_hours: 1,
      actual_hours: 0.5,
      status: 'partial',
    },
  ],
  summary: {
    total_planned_hours: 1,
    total_actual_hours: 0.5,
    done_count: 0,
    partial_count: 1,
    skipped_count: 0,
    unplanned_count: 0,
  },
}

const mockWeeklyResponse: WeeklyStatsResponse = {
  week_start: '2025-01-13',
  week_end: '2025-01-19',
  projects: [
    {
      project_id: 'proj-1',
      project_name: 'FlowDay',
      project_color: '#f59e0b',
      planned_hours: 10,
      actual_hours: 8,
      accuracy_pct: 80,
    },
  ],
  summary: {
    total_planned_hours: 10,
    total_actual_hours: 8,
    average_accuracy_pct: 80,
  },
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('usePlannedVsActual', () => {
  it('calls the correct endpoint with date query param', async () => {
    const { usePlannedVsActual } = await import('./analytics')
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDailyResponse,
    } as Response)

    const { result } = renderHook(() => usePlannedVsActual('2025-01-15'), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(vi.mocked(apiClient.get).mock.calls[0][0]).toBe(
      '/analytics/planned-vs-actual?date=2025-01-15',
    )
    expect(result.current.data?.tasks).toHaveLength(1)
    expect(result.current.data?.tasks[0].task_title).toBe('Write tests')
  })

  it('is disabled when date is empty', async () => {
    const { usePlannedVsActual } = await import('./analytics')

    const { result } = renderHook(() => usePlannedVsActual(''), { wrapper })

    expect(result.current.fetchStatus).toBe('idle')
    expect(vi.mocked(apiClient.get)).not.toHaveBeenCalled()
  })
})

describe('useWeeklyStats', () => {
  it('calls the correct endpoint with week_start query param', async () => {
    const { useWeeklyStats } = await import('./analytics')
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      ok: true,
      json: async () => mockWeeklyResponse,
    } as Response)

    const { result } = renderHook(() => useWeeklyStats('2025-01-13'), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(vi.mocked(apiClient.get).mock.calls[0][0]).toBe(
      '/analytics/weekly-stats?week_start=2025-01-13',
    )
    expect(result.current.data?.projects).toHaveLength(1)
    expect(result.current.data?.projects[0].project_name).toBe('FlowDay')
  })

  it('is disabled when weekStart is empty', async () => {
    const { useWeeklyStats } = await import('./analytics')

    const { result } = renderHook(() => useWeeklyStats(''), { wrapper })

    expect(result.current.fetchStatus).toBe('idle')
    expect(vi.mocked(apiClient.get)).not.toHaveBeenCalled()
  })
})
