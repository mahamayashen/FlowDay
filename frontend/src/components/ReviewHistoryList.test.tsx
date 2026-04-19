import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewHistoryList from './ReviewHistoryList'
import type { WeeklyReview } from '../types/weeklyReview'

const mockReviews: WeeklyReview[] = [
  {
    id: '1',
    user_id: 'u1',
    week_start: '2026-04-06',
    narrative: 'Week 1 was productive',
    insights_json: null,
    scores_json: { actionability: 80, accuracy: 70, coherence: 90 },
    status: 'complete',
    created_at: '2026-04-12T10:00:00Z',
  },
  {
    id: '2',
    user_id: 'u1',
    week_start: '2026-04-13',
    narrative: null,
    insights_json: null,
    scores_json: null,
    status: 'generating',
    created_at: '2026-04-19T10:00:00Z',
  },
]

describe('ReviewHistoryList', () => {
  it('renders the history list', () => {
    render(
      <ReviewHistoryList
        reviews={mockReviews}
        selectedWeekStart="2026-04-06"
        onSelectWeek={vi.fn()}
      />
    )
    expect(screen.getByTestId('review-history-list')).toBeInTheDocument()
  })

  it('renders an item for each review', () => {
    render(
      <ReviewHistoryList
        reviews={mockReviews}
        selectedWeekStart="2026-04-06"
        onSelectWeek={vi.fn()}
      />
    )
    expect(screen.getByTestId('review-history-item-2026-04-06')).toBeInTheDocument()
    expect(screen.getByTestId('review-history-item-2026-04-13')).toBeInTheDocument()
  })

  it('calls onSelectWeek when an item is clicked', async () => {
    const user = userEvent.setup()
    const onSelectWeek = vi.fn()
    render(
      <ReviewHistoryList
        reviews={mockReviews}
        selectedWeekStart="2026-04-06"
        onSelectWeek={onSelectWeek}
      />
    )
    await user.click(screen.getByTestId('review-history-item-2026-04-13'))
    expect(onSelectWeek).toHaveBeenCalledWith('2026-04-13')
  })

  it('shows empty state when no reviews', () => {
    render(
      <ReviewHistoryList reviews={[]} selectedWeekStart="" onSelectWeek={vi.fn()} />
    )
    expect(screen.getByTestId('review-history-empty')).toBeInTheDocument()
  })
})
