import React, { useEffect, useRef, useState } from 'react'
import { CaretLeft, CaretRight, Brain, Sparkle, ArrowClockwise } from '@phosphor-icons/react'
import JudgeScoreCard from '../components/JudgeScoreCard'
import ScoreTrendChart from '../components/ScoreTrendChart'
import ReviewHistoryList from '../components/ReviewHistoryList'
import AgentPipelineIndicator, {
  type AgentState,
  type AgentStatus,
} from '../components/AgentPipelineIndicator'
import { getWeekStart, formatLocalDate, addWeeks } from '../utils/reviewUtils'
import {
  mockWeeklyNarrative,
  mockJudgeScores,
  mockScoreTrend,
  mockReviewHistory,
} from '../mocks/data'
import type { WeeklyReview } from '../types/weeklyReview'
import './WeeklyReviewPage.css'

// ── Mock pipeline definition ──────────────────────────────────
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

// Convert mockScoreTrend shape (0–100 per dim) to the WeeklyReview[] the chart expects.
const trendAsReviews: WeeklyReview[] = mockScoreTrend.map((w, idx) => ({
  id: `mock-${idx}`,
  user_id: 'mock',
  week_start: w.week,
  narrative: null,
  insights_json: null,
  scores_json: {
    actionability: w.actionability / 10,
    accuracy:      w.accuracy / 10,
    coherence:     w.coherence / 10,
  },
  status: 'complete',
  created_at: w.week,
}))

// Scores for the selected week (shown in JudgeScoreCard) — 0–10 scale
const selectedScores = {
  actionability: mockJudgeScores.actionability / 10,
  accuracy:      mockJudgeScores.accuracy / 10,
  coherence:     mockJudgeScores.coherence / 10,
}

function WeeklyReviewPage(): React.JSX.Element {
  const [selectedWeekStart, setSelectedWeekStart] = useState<string>(() =>
    getWeekStart(formatLocalDate(new Date())),
  )

  // Generation simulation state
  const [isGenerating, setIsGenerating] = useState(false)
  const [hasGenerated, setHasGenerated]  = useState(true)    // start with the mock already rendered
  const [groupA,   setGroupA]   = useState<AgentState[]>(INITIAL_GROUP_A)
  const [groupBCD, setGroupBCD] = useState<AgentState[]>(INITIAL_GROUP_BCD)

  // Avoid double-schedules across StrictMode re-renders
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  function clearTimers(): void {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }

  useEffect(() => () => clearTimers(), [])

  function simulateGeneration(): void {
    clearTimers()
    setHasGenerated(false)
    setIsGenerating(true)
    setGroupA(INITIAL_GROUP_A.map((a) => ({ ...a, status: 'running' as AgentStatus })))
    setGroupBCD(INITIAL_GROUP_BCD.map((a) => ({ ...a })))

    const schedule = (ms: number, fn: () => void): void => {
      timersRef.current.push(setTimeout(fn, ms))
    }

    // Group A finishes together (parallel)
    schedule(1400, () => {
      setGroupA((prev) => prev.map((a) => ({ ...a, status: 'done' })))
      setGroupBCD((prev) =>
        prev.map((a, i) => ({ ...a, status: i === 0 ? 'running' : 'pending' })),
      )
    })

    // Pattern detector done → narrative writer running
    schedule(2400, () => {
      setGroupBCD((prev) =>
        prev.map((a, i) => ({
          ...a,
          status: i === 0 ? 'done' : i === 1 ? 'running' : 'pending',
        })),
      )
    })

    // Narrative writer done → judge running
    schedule(3600, () => {
      setGroupBCD((prev) =>
        prev.map((a, i) => ({
          ...a,
          status: i < 2 ? 'done' : 'running',
        })),
      )
    })

    // Judge done → reveal narrative
    schedule(4600, () => {
      setGroupBCD((prev) => prev.map((a) => ({ ...a, status: 'done' })))
      setIsGenerating(false)
      setHasGenerated(true)
    })
  }

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

          <button
            data-testid="generate-review-btn"
            className={`btn-primary weekly-generate-btn${isGenerating ? ' generating' : ''}`}
            disabled={isGenerating}
            onClick={simulateGeneration}
          >
            {isGenerating ? (
              <>
                <Sparkle size={14} weight="fill" />
                Generating…
              </>
            ) : (
              <>
                <ArrowClockwise size={13} />
                Regenerate
              </>
            )}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="weekly-review-body">
        {/* Pipeline indicator — always visible; more prominent during generation */}
        <AgentPipelineIndicator groupA={groupA} groupBCD={groupBCD} />

        <div className="weekly-review-grid">
          {/* Left column: narrative */}
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
                    Week of {selectedWeekStart} · Judge {Math.round(
                      (mockJudgeScores.actionability +
                        mockJudgeScores.accuracy +
                        mockJudgeScores.coherence) /
                        3,
                    )}/100
                  </span>
                </div>
              </header>

              {isGenerating && !hasGenerated && (
                <div className="weekly-narrative-placeholder">
                  <div className="skeleton-line" style={{ width: '92%' }} />
                  <div className="skeleton-line" style={{ width: '78%' }} />
                  <div className="skeleton-line" style={{ width: '88%' }} />
                  <div className="skeleton-line" style={{ width: '64%' }} />
                  <div className="skeleton-line" style={{ width: '80%' }} />
                </div>
              )}

              {hasGenerated && (
                <div className="weekly-narrative-body">
                  {mockWeeklyNarrative.split('\n\n').map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              )}
            </section>
          </div>

          {/* Right column: scores */}
          <div className="weekly-col-side">
            <JudgeScoreCard scores={hasGenerated ? selectedScores : null} />
            <div className="weekly-trend-card">
              <div className="ai-label">
                <Sparkle size={11} weight="fill" />
                Score Trend
              </div>
              <ScoreTrendChart reviews={trendAsReviews} />
            </div>
          </div>
        </div>

        {/* History */}
        <div className="weekly-history-section">
          <div className="review-section-title">Review history</div>
          <ReviewHistoryList
            reviews={mockReviewHistory.map((r) => ({
              id: r.id,
              user_id: 'mock',
              week_start: r.week_start,
              narrative: null,
              insights_json: null,
              scores_json: {
                actionability: r.avg_score / 10,
                accuracy:      r.avg_score / 10,
                coherence:     r.avg_score / 10,
              },
              status: 'complete',
              created_at: r.generated_at,
            }))}
            selectedWeekStart={selectedWeekStart}
            onSelectWeek={setSelectedWeekStart}
          />
        </div>
      </div>
    </main>
  )
}

export default WeeklyReviewPage
