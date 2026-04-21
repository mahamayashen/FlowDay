import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import React from 'react'

vi.stubGlobal('ResizeObserver', class {
  observe() {}
  unobserve() {}
  disconnect() {}
})

vi.mock('../api/analytics', () => ({
  usePlannedVsActual: vi.fn(() => ({ data: undefined, isLoading: false })),
  useWeeklyStats: vi.fn(() => ({ data: undefined, isLoading: false })),
}))

import { usePlannedVsActual, useWeeklyStats } from '../api/analytics'
import ReviewPage from './ReviewPage'
import type { PlannedVsActualResponse, WeeklyStatsResponse } from '../types/analytics'

const mockDaily: PlannedVsActualResponse = {
  date: '2026-04-19',
  tasks: [],
  summary: { total_planned_hours: 0, total_actual_hours: 0, done_count: 0, partial_count: 0, skipped_count: 0, unplanned_count: 0 },
}

const mockWeekly: WeeklyStatsResponse = {
  week_start: '2026-04-13',
  week_end: '2026-04-19',
  projects: [],
  summary: { total_planned_hours: 0, total_actual_hours: 0, average_accuracy_pct: 0 },
}

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(
    MemoryRouter,
    null,
    React.createElement(QueryClientProvider, { client: queryClient }, children),
  )
}

beforeEach(() => {
  vi.mocked(usePlannedVsActual).mockReturnValue({ data: mockDaily, isLoading: false } as ReturnType<typeof usePlannedVsActual>)
  vi.mocked(useWeeklyStats).mockReturnValue({ data: mockWeekly, isLoading: false } as ReturnType<typeof useWeeklyStats>)
})

describe('ReviewPage', () => {
  it('renders the page with testid', () => {
    render(<ReviewPage />, { wrapper })
    expect(screen.getByTestId('page-review')).toBeInTheDocument()
  })

  it('renders prev and next day navigation buttons', () => {
    render(<ReviewPage />, { wrapper })
    expect(screen.getByTestId('prev-day')).toBeInTheDocument()
    expect(screen.getByTestId('next-day')).toBeInTheDocument()
  })

  it('renders prev and next week navigation buttons', () => {
    render(<ReviewPage />, { wrapper })
    expect(screen.getByTestId('prev-week')).toBeInTheDocument()
    expect(screen.getByTestId('next-week')).toBeInTheDocument()
  })

  it('shows loading state while data is loading', () => {
    vi.mocked(usePlannedVsActual).mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof usePlannedVsActual>)
    vi.mocked(useWeeklyStats).mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useWeeklyStats>)
    render(<ReviewPage />, { wrapper })
    expect(screen.getByTestId('review-loading')).toBeInTheDocument()
  })

  it('shows empty state when both queries return empty lists', () => {
    render(<ReviewPage />, { wrapper })
    expect(screen.getByTestId('review-empty')).toBeInTheDocument()
  })

  it('shows error state when a query fails', () => {
    vi.mocked(usePlannedVsActual).mockReturnValue({ data: undefined, isLoading: false, isError: true } as ReturnType<typeof usePlannedVsActual>)
    vi.mocked(useWeeklyStats).mockReturnValue({ data: undefined, isLoading: false, isError: false } as ReturnType<typeof useWeeklyStats>)
    render(<ReviewPage />, { wrapper })
    expect(screen.getByTestId('review-error')).toBeInTheDocument()
    expect(screen.queryByTestId('review-empty')).not.toBeInTheDocument()
  })

  it('navigates to the next day when next-day button is clicked', async () => {
    const user = userEvent.setup()
    render(<ReviewPage />, { wrapper })
    const nextBtn = screen.getByTestId('next-day')
    const initialDate = screen.getByTestId('selected-date').textContent
    await user.click(nextBtn)
    expect(screen.getByTestId('selected-date').textContent).not.toBe(initialDate)
  })

  it('navigates to the previous week when prev-week button is clicked', async () => {
    const user = userEvent.setup()
    render(<ReviewPage />, { wrapper })
    const prevWeekBtn = screen.getByTestId('prev-week')
    const initialWeek = screen.getByTestId('selected-week').textContent
    await user.click(prevWeekBtn)
    expect(screen.getByTestId('selected-week').textContent).not.toBe(initialWeek)
  })
})
