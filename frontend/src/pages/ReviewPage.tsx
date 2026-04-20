import React, { useState } from 'react'
import { CaretLeft, CaretRight } from '@phosphor-icons/react'
import { usePlannedVsActual, useWeeklyStats } from '../api/analytics'
import DailyComparisonView from '../components/DailyComparisonView'
import WeeklyBarChart from '../components/WeeklyBarChart'
import { getWeekStart, toWeeklyChartData, formatLocalDate } from '../utils/reviewUtils'
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
            No data for this period.<br />
            <span>Start tracking tasks to see your review here.</span>
          </div>
        )}

        {!isLoading && !hasError && !isEmpty && (
          <div className="review-content">
            <section className="review-section">
              <h2 className="review-section-title">Daily Comparison</h2>
              <DailyComparisonView tasks={tasks} />
            </section>

            <section className="review-section">
              <h2 className="review-section-title">Weekly by Project</h2>
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
