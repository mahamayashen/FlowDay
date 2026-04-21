import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { WeeklyReview, JudgeScores } from '../types/weeklyReview'
import './ScoreTrendChart.css'

interface ScoreTrendChartProps {
  reviews: WeeklyReview[]
}

const COLOR_ACTIONABILITY = '#FFDE42' // yellow = focus/energy
const COLOR_ACCURACY = '#53CBF3'      // cyan = AI/insight
const COLOR_COHERENCE = '#5478FF'     // blue = interactive
const COLOR_GRID = 'rgba(255, 255, 255, 0.06)'
const COLOR_AXIS = 'rgba(255, 255, 255, 0.45)'

interface TooltipPayload {
  name?: string
  value?: number
  color?: string
  dataKey?: string
}

interface TooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string
}

function ChartTooltip({ active, payload, label }: TooltipProps): React.JSX.Element | null {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="score-tooltip">
      <div className="score-tooltip-label">Week of {label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="score-tooltip-row">
          <span className="score-tooltip-dot" style={{ background: entry.color }} />
          <span className="score-tooltip-key">{entry.name}</span>
          <span className="score-tooltip-value">{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

function ScoreTrendChart({ reviews }: ScoreTrendChartProps): React.JSX.Element {
  const chartData = reviews
    .filter((r): r is WeeklyReview & { scores_json: JudgeScores } => r.scores_json !== null)
    .map((r) => ({
      week: r.week_start,
      actionability: r.scores_json.actionability,
      accuracy: r.scores_json.accuracy,
      coherence: r.scores_json.coherence,
    }))

  if (chartData.length === 0) {
    return (
      <div data-testid="score-trend-empty" className="score-trend-empty">
        No score history available yet.
      </div>
    )
  }

  return (
    <div data-testid="score-trend-chart" className="score-trend-chart">
      <div className="score-trend-legend">
        <span className="score-trend-legend-item">
          <span className="score-trend-legend-dot" style={{ background: COLOR_ACTIONABILITY }} />
          Actionability
        </span>
        <span className="score-trend-legend-item">
          <span className="score-trend-legend-dot" style={{ background: COLOR_ACCURACY }} />
          Accuracy
        </span>
        <span className="score-trend-legend-item">
          <span className="score-trend-legend-dot" style={{ background: COLOR_COHERENCE }} />
          Coherence
        </span>
      </div>
      <div className="score-trend-canvas">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData} margin={{ top: 10, right: 18, left: 0, bottom: 4 }}>
            <CartesianGrid stroke={COLOR_GRID} strokeDasharray="3 3" />
            <XAxis
              dataKey="week"
              stroke={COLOR_AXIS}
              tick={{ fill: COLOR_AXIS, fontSize: 10, fontFamily: 'var(--font-mono)' }}
              tickLine={false}
              axisLine={{ stroke: COLOR_GRID }}
            />
            <YAxis
              domain={[0, 100]}
              stroke={COLOR_AXIS}
              tick={{ fill: COLOR_AXIS, fontSize: 10, fontFamily: 'var(--font-mono)' }}
              tickLine={false}
              axisLine={{ stroke: COLOR_GRID }}
            />
            <Tooltip
              content={<ChartTooltip />}
              cursor={{ stroke: 'rgba(84, 120, 255, 0.3)', strokeWidth: 1 }}
            />
            <Line
              type="monotone"
              dataKey="actionability"
              name="Actionability"
              stroke={COLOR_ACTIONABILITY}
              strokeWidth={2}
              dot={{ r: 3, fill: COLOR_ACTIONABILITY, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: COLOR_ACTIONABILITY, stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="accuracy"
              name="Accuracy"
              stroke={COLOR_ACCURACY}
              strokeWidth={2}
              dot={{ r: 3, fill: COLOR_ACCURACY, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: COLOR_ACCURACY, stroke: '#0a0e1a', strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="coherence"
              name="Coherence"
              stroke={COLOR_COHERENCE}
              strokeWidth={2}
              dot={{ r: 3, fill: COLOR_COHERENCE, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: COLOR_COHERENCE, stroke: '#0a0e1a', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ScoreTrendChart
