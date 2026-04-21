import React, { useState } from 'react'
import { CaretLeft, CaretRight, Sparkle, ArrowClockwise } from '@phosphor-icons/react'
import { usePlannedVsActual, useWeeklyStats } from '../api/analytics'
import DailyComparisonView from '../components/DailyComparisonView'
import WeeklyBarChart from '../components/WeeklyBarChart'
import { getWeekStart, toWeeklyChartData, formatLocalDate } from '../utils/reviewUtils'
import { mockDailyNarrative } from '../mocks/data'
import './ReviewPage.css'

function addDays(date: string, days: number): string {
  const d = new Date(date + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return formatLocalDate(d)
}

function today(): string {
  return formatLocalDate(new Date())
}

function ReviewPage(): React.JSX.Element {
  const [selectedDate, setSelectedDate] = useState<string>(today)
  const [weekStart, setWeekStart] = useState<string>(() => getWeekStart(today()))

  const dailyQuery = usePlannedVsActual(selectedDate)
  const weeklyQuery = useWeeklyStats(weekStart)

  const isLoading = dailyQuery.isLoading || weeklyQuery.isLoading
  const hasError = dailyQuery.isError || weeklyQuery.isError

  const tasks = dailyQuery.data?.tasks ?? []
  const projects = weeklyQuery.data?.projects ?? []
  const isEmpty = !isLoading && !hasError && tasks.length === 0 && projects.length === 0

  return (
    <main data-testid="page-review" className="review-page">
      {/* Header */}
      <div className="review-header">
        <div className="review-nav-row">
          {/* Day navigator */}
          <div className="review-nav-group">
            <span className="review-nav-label">Day</span>
            <div className="review-nav-controls">
              <button
                data-testid="prev-day"
                className="date-nav-btn"
                onClick={() => setSelectedDate((d) => addDays(d, -1))}
                aria-label="Previous day"
              >
                <CaretLeft size={14} />
              </button>
              <span data-testid="selected-date" className="review-date-display">
                {selectedDate}
              </span>
              <button
                data-testid="next-day"
                className="date-nav-btn"
                onClick={() => setSelectedDate((d) => addDays(d, 1))}
                aria-label="Next day"
              >
                <CaretRight size={14} />
              </button>
            </div>
          </div>

          <div className="review-nav-divider" />

          {/* Week navigator */}
          <div className="review-nav-group">
            <span className="review-nav-label">Week</span>
            <div className="review-nav-controls">
              <button
                data-testid="prev-week"
                className="date-nav-btn"
                onClick={() => setWeekStart((w) => addDays(w, -7))}
                aria-label="Previous week"
              >
                <CaretLeft size={14} />
              </button>
              <span data-testid="selected-week" className="review-date-display">
                {weekStart}
              </span>
              <button
                data-testid="next-week"
                className="date-nav-btn"
                onClick={() => setWeekStart((w) => addDays(w, 7))}
                aria-label="Next week"
              >
                <CaretRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="review-body">
        {/* AI daily summary — always visible at the top */}
        <section className="review-ai-card" data-testid="review-ai-summary">
          <div className="review-ai-head">
            <div className="review-ai-title-group">
              <Sparkle size={16} color="var(--cyan)" weight="fill" />
              <h2 className="review-ai-title">AI daily summary</h2>
              <span className="review-ai-tag">Narrative Writer · Judge 89/100</span>
            </div>
            <button className="review-ai-regen" type="button">
              <ArrowClockwise size={12} />
              Regenerate
            </button>
          </div>
          <p className="review-ai-body">{mockDailyNarrative}</p>
        </section>

        {isLoading && (
          <p data-testid="review-loading" className="loading-text">Loading...</p>
        )}

        {hasError && (
          <p data-testid="review-error" className="error-text">
            Failed to load data. Please try again.
          </p>
        )}

        {isEmpty && (
          <div data-testid="review-empty" className="empty-state">
            No tracked data for this period yet.<br />
            <span>Start a timer from Today to see planned-vs-actual here.</span>
          </div>
        )}

        {!isLoading && !hasError && !isEmpty && (
          <div className="review-content">
            <section className="review-section">
              <h2 className="review-section-title">Planned vs actual</h2>
              <DailyComparisonView tasks={tasks} />
            </section>

            <section className="review-section">
              <h2 className="review-section-title">Weekly by project</h2>
              <div className="review-chart-card">
                <WeeklyBarChart data={toWeeklyChartData(projects)} />
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  )
}

export default ReviewPage
