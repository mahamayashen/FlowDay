import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

vi.stubGlobal('ResizeObserver', class {
  observe() {}
  unobserve() {}
  disconnect() {}
})

vi.mock('../api/weeklyReviews', () => ({
  useWeeklyReview: vi.fn(() => ({ data: undefined, isLoading: false, isError: false })),
  useWeeklyReviewHistory: vi.fn(() => ({ data: [], isLoading: false })),
  useGenerateWeeklyReview: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}))

import {
  useWeeklyReview,
  useWeeklyReviewHistory,
  useGenerateWeeklyReview,
} from '../api/weeklyReviews'
import WeeklyReviewPage from './WeeklyReviewPage'
import type { WeeklyReview } from '../types/weeklyReview'

const mockReview: WeeklyReview = {
  id: '1',
  user_id: 'u1',
  week_start: '2026-04-13',
  narrative: 'This was a productive week.',
  insights_json: null,
  scores_json: { actionability: 85, accuracy: 72, coherence: 91 },
  status: 'complete',
  created_at: '2026-04-19T10:00:00Z',
}

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  vi.mocked(useWeeklyReview).mockReturnValue({
    data: mockReview,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useWeeklyReview>)
  vi.mocked(useWeeklyReviewHistory).mockReturnValue({
    data: [mockReview],
    isLoading: false,
  } as ReturnType<typeof useWeeklyReviewHistory>)
  vi.mocked(useGenerateWeeklyReview).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useGenerateWeeklyReview>)
})

describe('WeeklyReviewPage', () => {
  it('renders the page', () => {
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('page-weekly-review')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('weekly-review-loading')).toBeInTheDocument()
  })

  it('shows error state', () => {
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('weekly-review-error')).toBeInTheDocument()
  })

  it('renders narrative when review is complete', () => {
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('narrative-content')).toBeInTheDocument()
  })

  it('renders judge scores when review is complete', () => {
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('judge-score-card')).toBeInTheDocument()
  })

  it('renders review history list', () => {
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('review-history-list')).toBeInTheDocument()
  })

  it('hides generate button during loading', () => {
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.queryByTestId('generate-review-btn')).not.toBeInTheDocument()
  })

  it('hides generate button during error', () => {
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.queryByTestId('generate-review-btn')).not.toBeInTheDocument()
  })

  it('shows generate button when no review exists', () => {
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('generate-review-btn')).toBeInTheDocument()
  })

  it('calls mutate when generate button is clicked', async () => {
    const user = userEvent.setup()
    const mutateFn = vi.fn()
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useWeeklyReview>)
    vi.mocked(useGenerateWeeklyReview).mockReturnValue({
      mutate: mutateFn,
      isPending: false,
    } as unknown as ReturnType<typeof useGenerateWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    await user.click(screen.getByTestId('generate-review-btn'))
    expect(mutateFn).toHaveBeenCalled()
  })

  it('disables generate button when generating', () => {
    vi.mocked(useWeeklyReview).mockReturnValue({
      data: { ...mockReview, status: 'generating', narrative: null, scores_json: null },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useWeeklyReview>)
    vi.mocked(useGenerateWeeklyReview).mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useGenerateWeeklyReview>)
    render(<WeeklyReviewPage />, { wrapper })
    expect(screen.getByTestId('generate-review-btn')).toBeDisabled()
  })

  it('navigates to the previous week', async () => {
    const user = userEvent.setup()
    render(<WeeklyReviewPage />, { wrapper })
    const initialWeek = screen.getByTestId('selected-week').textContent
    await user.click(screen.getByTestId('prev-week'))
    expect(screen.getByTestId('selected-week').textContent).not.toBe(initialWeek)
  })

  it('navigates to the next week', async () => {
    const user = userEvent.setup()
    render(<WeeklyReviewPage />, { wrapper })
    const initialWeek = screen.getByTestId('selected-week').textContent
    await user.click(screen.getByTestId('next-week'))
    expect(screen.getByTestId('selected-week').textContent).not.toBe(initialWeek)
  })
})
