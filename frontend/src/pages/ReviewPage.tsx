import React, { useState } from 'react'
import { usePlannedVsActual, useWeeklyStats } from '../api/analytics'
import DailyComparisonView from '../components/DailyComparisonView'
import WeeklyBarChart from '../components/WeeklyBarChart'
import { getWeekStart, toWeeklyChartData } from '../utils/reviewUtils'

function addDays(date: string, days: number): string {
  const d = new Date(date + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function ReviewPage(): React.JSX.Element {
  const [selectedDate, setSelectedDate] = useState<string>(today)
  const [weekStart, setWeekStart] = useState<string>(() => getWeekStart(today()))

  const dailyQuery = usePlannedVsActual(selectedDate)
  const weeklyQuery = useWeeklyStats(weekStart)

  const isLoading = dailyQuery.isLoading || weeklyQuery.isLoading

  const tasks = dailyQuery.data?.tasks ?? []
  const projects = weeklyQuery.data?.projects ?? []
  const isEmpty = !isLoading && tasks.length === 0 && projects.length === 0

  return (
    <main data-testid="page-review">
      <section>
        <div>
          <button data-testid="prev-day" onClick={() => setSelectedDate((d) => addDays(d, -1))}>
            &lt;
          </button>
          <span data-testid="selected-date">{selectedDate}</span>
          <button data-testid="next-day" onClick={() => setSelectedDate((d) => addDays(d, 1))}>
            &gt;
          </button>
        </div>
        <div>
          <button data-testid="prev-week" onClick={() => setWeekStart((w) => addDays(w, -7))}>
            &lt;&lt;
          </button>
          <span data-testid="selected-week">{weekStart}</span>
          <button data-testid="next-week" onClick={() => setWeekStart((w) => addDays(w, 7))}>
            &gt;&gt;
          </button>
        </div>
      </section>

      {isLoading && <div data-testid="review-loading">Loading...</div>}

      {isEmpty && (
        <div data-testid="review-empty">No data for this period</div>
      )}

      {!isLoading && !isEmpty && (
        <>
          <DailyComparisonView tasks={tasks} />
          <WeeklyBarChart data={toWeeklyChartData(projects)} />
        </>
      )}
    </main>
  )
}

export default ReviewPage
