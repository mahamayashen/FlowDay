import React from 'react'
import type { WeeklyReview, ReviewStatus } from '../types/weeklyReview'

const STATUS_COLORS: Record<ReviewStatus, string> = {
  complete: '#22c55e',
  generating: '#f59e0b',
  failed: '#ef4444',
  pending: '#6b7280',
}

interface ReviewHistoryListProps {
  reviews: WeeklyReview[]
  selectedWeekStart: string
  onSelectWeek: (weekStart: string) => void
}

function ReviewHistoryList({
  reviews,
  selectedWeekStart,
  onSelectWeek,
}: ReviewHistoryListProps): React.JSX.Element {
  if (reviews.length === 0) {
    return <div data-testid="review-history-empty">No review history yet.</div>
  }

  return (
    <ul data-testid="review-history-list">
      {reviews.map((review) => (
        <li
          key={review.week_start}
          data-testid={`review-history-item-${review.week_start}`}
          role="button"
          tabIndex={0}
          onClick={() => onSelectWeek(review.week_start)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onSelectWeek(review.week_start)
          }}
          style={{
            cursor: 'pointer',
            fontWeight: review.week_start === selectedWeekStart ? 'bold' : 'normal',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: STATUS_COLORS[review.status],
              marginRight: 6,
            }}
          />
          {review.week_start} — {review.status}
          {review.narrative && (
            <span> — {review.narrative.slice(0, 60)}</span>
          )}
        </li>
      ))}
    </ul>
  )
}

export default ReviewHistoryList
