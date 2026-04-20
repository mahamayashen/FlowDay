import React, { useState } from 'react'
import { CaretLeft, CaretRight, Brain, Sparkle } from '@phosphor-icons/react'
import { useWeeklyReview, useWeeklyReviewHistory, useGenerateWeeklyReview } from '../api/weeklyReviews'
import NarrativeSection from '../components/NarrativeSection'
import JudgeScoreCard from '../components/JudgeScoreCard'
import ScoreTrendChart from '../components/ScoreTrendChart'
import ReviewHistoryList from '../components/ReviewHistoryList'
import { getWeekStart, formatLocalDate, addWeeks } from '../utils/reviewUtils'
import './WeeklyReviewPage.css'

function WeeklyReviewPage(): React.JSX.Element {
  const [selectedWeekStart, setSelectedWeekStart] = useState<string>(() =>
    getWeekStart(formatLocalDate(new Date()))
  )

  const reviewQuery = useWeeklyReview(selectedWeekStart)
  const historyQuery = useWeeklyReviewHistory(10)
  const generateMutation = useGenerateWeeklyReview()

  const review = reviewQuery.data
  const history = historyQuery.data ?? []

  const isGenerating = review?.status === 'generating' || generateMutation.isPending
  const buttonLabel =
    !review || review.status === 'pending' ? 'Generate Review' : 'Regenerate'

  return (
    <main data-testid="page-weekly-review" className="weekly-review-page">
      {/* Header */}
      <div className="weekly-review-header">
        <div className="weekly-review-title-row">
          <div className="weekly-review-title">
            <Brain size={18} color="var(--cyan)" weight="fill" />
            AI Weekly Review
          </div>

          <div className="weekly-review-nav">
            <button
              data-testid="prev-week"
              className="date-nav-btn"
              onClick={() => setSelectedWeekStart((w) => addWeeks(w, -1))}
              aria-label="Previous week"
            >
              <CaretLeft size={14} />
            </button>
            <span data-testid="selected-week" className="weekly-nav-date">
              {selectedWeekStart}
            </span>
            <button
              data-testid="next-week"
              className="date-nav-btn"
              onClick={() => setSelectedWeekStart((w) => addWeeks(w, 1))}
              aria-label="Next week"
            >
              <CaretRight size={14} />
            </button>
          </div>

          {!reviewQuery.isLoading && !reviewQuery.isError && (
            <button
              data-testid="generate-review-btn"
              className={`btn btn-primary weekly-generate-btn${isGenerating ? ' generating' : ''}`}
              disabled={isGenerating}
              onClick={() => generateMutation.mutate(selectedWeekStart)}
            >
              <Sparkle size={14} weight="fill" />
              {isGenerating ? 'Generating…' : buttonLabel}
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="weekly-review-body">
        {reviewQuery.isLoading && (
          <p data-testid="weekly-review-loading" className="loading-text">
            Loading…
          </p>
        )}

        {reviewQuery.isError && (
          <p data-testid="weekly-review-error" className="error-text">
            Failed to load review. Please try again.
          </p>
        )}

        {!reviewQuery.isLoading && !reviewQuery.isError && (
          <div className="weekly-review-grid">
            {/* Left column: narrative */}
            <div className="weekly-col-main">
              <NarrativeSection
                narrative={review?.narrative ?? null}
                status={review?.status ?? 'pending'}
              />
            </div>

            {/* Right column: scores */}
            <div className="weekly-col-side">
              <JudgeScoreCard scores={review?.scores_json ?? null} />
              <div className="weekly-trend-card">
                <div className="ai-label">
                  <Sparkle size={11} weight="fill" />
                  Score Trend
                </div>
                <ScoreTrendChart reviews={history} />
              </div>
            </div>
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div className="weekly-history-section">
            <div className="review-section-title">Review History</div>
            <ReviewHistoryList
              reviews={history}
              selectedWeekStart={selectedWeekStart}
              onSelectWeek={setSelectedWeekStart}
            />
          </div>
        )}
      </div>
    </main>
  )
}

export default WeeklyReviewPage
