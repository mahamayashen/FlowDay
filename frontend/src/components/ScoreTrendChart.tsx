import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { WeeklyReview } from '../types/weeklyReview'

interface ScoreTrendChartProps {
  reviews: WeeklyReview[]
}

function ScoreTrendChart({ reviews }: ScoreTrendChartProps): React.JSX.Element {
  const chartData = reviews
    .filter((r) => r.scores_json !== null)
    .map((r) => ({
      week: r.week_start,
      actionability: r.scores_json!.actionability,
      accuracy: r.scores_json!.accuracy,
      coherence: r.scores_json!.coherence,
    }))

  if (chartData.length === 0) {
    return <div data-testid="score-trend-empty">No score history available yet.</div>
  }

  return (
    <div data-testid="score-trend-chart">
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <XAxis dataKey="week" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="actionability" stroke="#f59e0b" />
          <Line type="monotone" dataKey="accuracy" stroke="#22c55e" />
          <Line type="monotone" dataKey="coherence" stroke="#60a5fa" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ScoreTrendChart
