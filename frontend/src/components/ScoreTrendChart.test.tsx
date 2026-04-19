import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ScoreTrendChart from './ScoreTrendChart'
import type { WeeklyReview } from '../types/weeklyReview'

vi.stubGlobal('ResizeObserver', class {
  observe() {}
  unobserve() {}
  disconnect() {}
})

const mockReviews: WeeklyReview[] = [
  {
    id: '1',
    user_id: 'u1',
    week_start: '2026-04-06',
    narrative: 'Week 1',
    insights_json: null,
    scores_json: { actionability: 80, accuracy: 70, coherence: 90 },
    status: 'complete',
    created_at: '2026-04-12T10:00:00Z',
  },
  {
    id: '2',
    user_id: 'u1',
    week_start: '2026-04-13',
    narrative: 'Week 2',
    insights_json: null,
    scores_json: { actionability: 85, accuracy: 75, coherence: 88 },
    status: 'complete',
    created_at: '2026-04-19T10:00:00Z',
  },
]

describe('ScoreTrendChart', () => {
  it('shows empty state when no complete reviews', () => {
    render(<ScoreTrendChart reviews={[]} />)
    expect(screen.getByTestId('score-trend-empty')).toBeInTheDocument()
  })

  it('renders the chart when reviews with scores exist', () => {
    render(<ScoreTrendChart reviews={mockReviews} />)
    expect(screen.getByTestId('score-trend-chart')).toBeInTheDocument()
  })

  it('filters out reviews without scores', () => {
    const reviewWithoutScores: WeeklyReview = {
      ...mockReviews[0],
      id: '3',
      scores_json: null,
      status: 'pending',
    }
    render(<ScoreTrendChart reviews={[reviewWithoutScores]} />)
    expect(screen.getByTestId('score-trend-empty')).toBeInTheDocument()
  })
})
