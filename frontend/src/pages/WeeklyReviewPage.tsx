import React, { useEffect, useRef, useState } from 'react'
import { CaretLeft, CaretRight, Brain, Sparkle, ArrowClockwise } from '@phosphor-icons/react'
import JudgeScoreCard from '../components/JudgeScoreCard'
import ScoreTrendChart from '../components/ScoreTrendChart'
import ReviewHistoryList from '../components/ReviewHistoryList'
import AgentPipelineIndicator, {
  type AgentState,
  type AgentStatus,
} from '../components/AgentPipelineIndicator'
import {
  useWeeklyReview,
  useWeeklyReviewHistory,
  useGenerateWeeklyReview,
} from '../api/weeklyReviews'
import { getWeekStart, formatLocalDate, addWeeks } from '../utils/reviewUtils'
import './WeeklyReviewPage.css'

// ── Pipeline definition ───────────────────────────────────────
const INITIAL_GROUP_A: AgentState[] = [
  { name: 'time_agent',    label: 'Time',    status: 'pending' },
  { name: 'meeting_agent', label: 'Meeting', status: 'pending' },
  { name: 'code_agent',    label: 'Code',    status: 'pending' },
  { name: 'task_agent',    label: 'Task',    status: 'pending' },
]

const INITIAL_GROUP_BCD: AgentState[] = [
  { name: 'pattern_detector',  label: 'Pattern Detector',  status: 'pending' },
  { name: 'narrative_writer',  label: 'Narrative Writer',  status: 'pending' },
  { name: 'judge',             label: 'Judge',             status: 'pending' },
]

function bcdStatuses(done: number, running: number | null): AgentState[] {
  return INITIAL_GROUP_BCD.map((a, i) => ({
    ...a,
    status: (i < done ? 'done' : i === running ? 'running' : 'pending') as AgentStatus,
  }))
}

function allRunning(initial: AgentState[]): AgentState[] {
  return initial.map((a) => ({ ...a, status: 'running' as AgentStatus }))
}

function allDone(initial: AgentState[]): AgentState[] {
  return initial.map((a) => ({ ...a, status: 'done' as AgentStatus }))
}

function WeeklyReviewPage(): React.JSX.Element {
  const [selectedWeekStart, setSelectedWeekStart] = useState<string>(() =>
    getWeekStart(formatLocalDate(new Date())),
  )

  const reviewQuery     = useWeeklyReview(selectedWeekStart)
  const historyQuery    = useWeeklyReviewHistory(10)
  const generateMutation = useGenerateWeeklyReview()

  const review  = reviewQuery.data
  const history = historyQuery.data ?? []

  const isGenerating = generateMutation.isPending || review?.status === 'generating'
  const hasReview    = review != null && review.status === 'complete'

  // ── Pipeline animation state ─────────────────────────────────
  const [groupA,   setGroupA]   = useState<AgentState[]>(INITIAL_GROUP_A)
  const [groupBCD, setGroupBCD] = useState<AgentState[]>(INITIAL_GROUP_BCD)
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  function clearTimers(): void {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }

  useEffect(() => () => clearTimers(), [])

  // Drive the fake pipeline off the real mutation lifecycle.
  // Backend /generate blocks for the full A→B→C→D run (10–30s), so we
  // simply fake-advance the chips on a timeline and snap them to "done"
  // when the response returns. If the response lands earlier than the
  // fake timeline, the effect re-fires with isGenerating=false and sets
  // everything to done.
  useEffect(() => {
    clearTimers()

    if (!isGenerating) {
      if (hasReview) {
        setGroupA(allDone(INITIAL_GROUP_A))
        setGroupBCD(allDone(INITIAL_GROUP_BCD))
      } else {
        setGroupA(INITIAL_GROUP_A)
        setGroupBCD(INITIAL_GROUP_BCD)
      }
      return
    }

    // Stage 0 (immediately): all Group A running, BCD pending
    setGroupA(allRunning(INITIAL_GROUP_A))
    setGroupBCD(bcdStatuses(0, null))

    // Stage 1 @ 4s: Group A done, Pattern Detector running
    timersRef.current.push(
      setTimeout(() => {
        setGroupA(allDone(INITIAL_GROUP_A))
        setGroupBCD(bcdStatuses(0, 0))
      }, 4_000),
    )
    // Stage 2 @ 10s: Pattern Detector done, Narrative Writer running
    timersRef.current.push(
      setTimeout(() => {
        setGroupBCD(bcdStatuses(1, 1))
      }, 10_000),
    )
    // Stage 3 @ 18s: Narrative Writer done, Judge running
    timersRef.current.push(
      setTimeout(() => {
        setGroupBCD(bcdStatuses(2, 2))
      }, 18_000),
    )
    // Stage 4 @ 26s: Judge also running — if backend takes longer, pulse
    // it and wait. When the real response returns, the effect resets and
    // snaps everything to done.
  }, [isGenerating, hasReview])

  function handleGenerate(): void {
    generateMutation.mutate(selectedWeekStart)
  }

  const buttonLabel = !review || review.status === 'pending' ? 'Generate review' : 'Regenerate'
  const judgeAvg =
    review?.scores_json
      ? Math.round(
          (review.scores_json.actionability +
            review.scores_json.accuracy +
            review.scores_json.coherence) / 3 * 10,
        )
      : null

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
              className={`btn-primary weekly-generate-btn${isGenerating ? ' generating' : ''}`}
              disabled={isGenerating}
              onClick={handleGenerate}
            >
              {isGenerating ? (
                <>
                  <Sparkle size={14} weight="fill" />
                  Generating…
                </>
              ) : review ? (
                <>
                  <ArrowClockwise size={13} />
                  {buttonLabel}
                </>
              ) : (
                <>
                  <Sparkle size={14} weight="fill" />
                  {buttonLabel}
                </>
              )}
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
          <>
            {/* Pipeline indicator — always visible, more prominent while running */}
            <AgentPipelineIndicator groupA={groupA} groupBCD={groupBCD} />

            <div className="weekly-review-grid">
              <div className="weekly-col-main">
                <section
                  className="weekly-narrative-card"
                  data-testid="weekly-narrative"
                  aria-busy={isGenerating}
                >
                  <header className="weekly-narrative-head">
                    <div className="weekly-narrative-title-group">
                      <Sparkle size={14} weight="fill" color="var(--cyan)" />
                      <span className="weekly-narrative-title">Narrative Writer</span>
                      <span className="weekly-narrative-tag">
                        Week of {selectedWeekStart}
                        {judgeAvg != null && ` · Judge ${judgeAvg}/100`}
                      </span>
                    </div>
                  </header>

                  {isGenerating && (
                    <div className="weekly-narrative-placeholder">
                      <div className="skeleton-line" style={{ width: '92%' }} />
                      <div className="skeleton-line" style={{ width: '78%' }} />
                      <div className="skeleton-line" style={{ width: '88%' }} />
                      <div className="skeleton-line" style={{ width: '64%' }} />
                      <div className="skeleton-line" style={{ width: '80%' }} />
                    </div>
                  )}

                  {!isGenerating && review?.narrative && (
                    <div
                      data-testid="narrative-content"
                      className="weekly-narrative-body"
                    >
                      {review.narrative.split(/\n\n+/).map((para, i) => (
                        <p key={i}>{para}</p>
                      ))}
                    </div>
                  )}

                  {!isGenerating && !review?.narrative && (
                    <p
                      data-testid="narrative-content"
                      className="weekly-narrative-empty"
                    >
                      No review has been generated for this week yet. Click
                      "Generate review" above to kick off the AI pipeline —
                      it takes 10–30 seconds.
                    </p>
                  )}
                </section>
              </div>

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

            <div className="weekly-history-section">
              <div className="review-section-title">Review history</div>
              <ReviewHistoryList
                reviews={history}
                selectedWeekStart={selectedWeekStart}
                onSelectWeek={setSelectedWeekStart}
              />
            </div>
          </>
        )}
      </div>
    </main>
  )
}

export default WeeklyReviewPage
