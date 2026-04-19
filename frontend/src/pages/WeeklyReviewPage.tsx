import React, { useState } from 'react'
import { useWeeklyReview, useWeeklyReviewHistory, useGenerateWeeklyReview } from '../api/weeklyReviews'
import NarrativeSection from '../components/NarrativeSection'
import JudgeScoreCard from '../components/JudgeScoreCard'
import ScoreTrendChart from '../components/ScoreTrendChart'
import ReviewHistoryList from '../components/ReviewHistoryList'
import { getWeekStart, formatLocalDate } from '../utils/reviewUtils'

function addWeeks(weekStart: string, weeks: number): string {
  const d = new Date(weekStart + 'T00:00:00')
  d.setDate(d.getDate() + weeks * 7)
  return formatLocalDate(d)
}

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
    <main data-testid="page-weekly-review">
      <section>
        <button
          data-testid="prev-week"
          onClick={() => setSelectedWeekStart((w) => addWeeks(w, -1))}
        >
          {'<<'}
        </button>
        <span data-testid="selected-week">{selectedWeekStart}</span>
        <button
          data-testid="next-week"
          onClick={() => setSelectedWeekStart((w) => addWeeks(w, 1))}
        >
          {'>>'}
        </button>
      </section>

      <button
        data-testid="generate-review-btn"
        disabled={isGenerating}
        onClick={() => generateMutation.mutate(selectedWeekStart)}
      >
        {buttonLabel}
      </button>

      {reviewQuery.isLoading && (
        <div data-testid="weekly-review-loading">Loading...</div>
      )}

      {reviewQuery.isError && (
        <div data-testid="weekly-review-error">Failed to load review. Please try again.</div>
      )}

      {!reviewQuery.isLoading && !reviewQuery.isError && (
        <>
          <NarrativeSection
            narrative={review?.narrative ?? null}
            status={review?.status ?? 'pending'}
          />
          <JudgeScoreCard scores={review?.scores_json ?? null} />
        </>
      )}

      <ScoreTrendChart reviews={history} />
      <ReviewHistoryList
        reviews={history}
        selectedWeekStart={selectedWeekStart}
        onSelectWeek={setSelectedWeekStart}
      />
    </main>
  )
}

export default WeeklyReviewPage
