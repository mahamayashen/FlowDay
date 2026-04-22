import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { CaretLeft, CaretRight, Sparkle } from '@phosphor-icons/react'
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

function formatWeekRange(weekStartStr: string): string {
  const start = new Date(weekStartStr + 'T00:00:00')
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  const fmt = (d: Date) =>
    d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  return `${fmt(start)} – ${fmt(end)}`
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

function ReviewPage(): React.JSX.Element {
  const [selectedDate, setSelectedDate] = useState<string>(today)
  const [weekStart, setWeekStart] = useState<string>(() => getWeekStart(today()))

  const dailyQuery = usePlannedVsActual(selectedDate)
  const weeklyQuery = useWeeklyStats(weekStart)

  const tasks = dailyQuery.data?.tasks ?? []
  const projects = weeklyQuery.data?.projects ?? []

  return (
    <main data-testid="page-review" className="review-page">
      <div className="review-body">
        {/* AI summary pointer — FlowDay's AI review is weekly, not daily */}
        <section className="review-ai-card" data-testid="review-ai-summary">
          <div className="review-ai-head">
            <div className="review-ai-title-group">
              <Sparkle size={16} color="var(--cyan)" weight="fill" />
              <h2 className="review-ai-title">AI review</h2>
              <span className="review-ai-tag">Weekly narrative + Judge scores</span>
            </div>
          </div>
          <p className="review-ai-body">
            FlowDay's AI digests your whole week at once — patterns, drift, estimation
            accuracy — instead of a daily rehash. Head to the weekly view to generate one.
          </p>
          <Link to="/weekly" className="review-ai-link">
            Open weekly review →
          </Link>
        </section>

        {/* ── Day-scoped section ───────────────────────────────── */}
        <section className="review-section">
          <header className="review-section-head">
            <div className="review-section-title-block">
              <span className="review-nav-label">Day</span>
              <h2 className="review-section-title">Planned vs actual</h2>
            </div>
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
                {formatDateLabel(selectedDate)}
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
          </header>

          {dailyQuery.isLoading && (
            <p data-testid="day-loading" className="loading-text">
              Loading daily comparison…
            </p>
          )}
          {dailyQuery.isError && (
            <p data-testid="day-error" className="error-text">
              Failed to load daily data.
            </p>
          )}
          {!dailyQuery.isLoading && !dailyQuery.isError && tasks.length === 0 && (
            <div data-testid="day-empty" className="empty-state">
              No tasks tracked or scheduled on this day.
            </div>
          )}
          {!dailyQuery.isLoading && !dailyQuery.isError && tasks.length > 0 && (
            <DailyComparisonView tasks={tasks} />
          )}
        </section>

        {/* ── Week-scoped section ──────────────────────────────── */}
        <section className="review-section">
          <header className="review-section-head">
            <div className="review-section-title-block">
              <span className="review-nav-label">Week</span>
              <h2 className="review-section-title">Weekly by project</h2>
            </div>
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
                {formatWeekRange(weekStart)}
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
          </header>

          {weeklyQuery.isLoading && (
            <p data-testid="week-loading" className="loading-text">
              Loading weekly stats…
            </p>
          )}
          {weeklyQuery.isError && (
            <p data-testid="week-error" className="error-text">
              Failed to load weekly data.
            </p>
          )}
          {!weeklyQuery.isLoading && !weeklyQuery.isError && projects.length === 0 && (
            <div data-testid="week-empty" className="empty-state">
              No projects with tracked or planned hours in this week.
            </div>
          )}
          {!weeklyQuery.isLoading && !weeklyQuery.isError && projects.length > 0 && (
            <WeeklyBarChart data={toWeeklyChartData(projects)} />
          )}
        </section>
      </div>
    </main>
  )
}

export default ReviewPage
