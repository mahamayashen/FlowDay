import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import type { WeeklyChartEntry } from '../types/analytics'
import './WeeklyBarChart.css'

interface WeeklyBarChartProps {
  data: WeeklyChartEntry[]
}

// Design tokens (kept as literals because recharts consumes strings synchronously)
const COLOR_PLANNED = '#5478FF'
const COLOR_ACTUAL = '#FFDE42'
const COLOR_GRID = 'rgba(255, 255, 255, 0.06)'
const COLOR_AXIS = 'rgba(255, 255, 255, 0.45)'

interface TooltipPayload {
  name?: string
  value?: number | string
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
    <div className="weekly-tooltip">
      <div className="weekly-tooltip-label">{label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="weekly-tooltip-row">
          <span className="weekly-tooltip-dot" style={{ background: entry.color }} />
          <span className="weekly-tooltip-key">{entry.name}</span>
          <span className="weekly-tooltip-value">
            {typeof entry.value === 'number' ? `${entry.value}h` : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

function WeeklyBarChart({ data }: WeeklyBarChartProps): React.JSX.Element {
  if (data.length === 0) {
    return <p className="weekly-empty">No project data for this week</p>
  }

  // Keep a visually-hidden project list for a11y + tests
  return (
    <div data-testid="weekly-bar-chart" className="weekly-bar-chart">
      <ul aria-label="project list" className="weekly-a11y-list">
        {data.map((entry) => (
          <li key={entry.name}>{entry.name}</li>
        ))}
      </ul>

      <div className="weekly-legend">
        <span className="weekly-legend-item">
          <span className="weekly-legend-dot weekly-legend-dot--planned" />
          Planned
        </span>
        <span className="weekly-legend-item">
          <span className="weekly-legend-dot weekly-legend-dot--actual" />
          Actual
        </span>
      </div>

      <div aria-hidden="true" className="weekly-chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 10, right: 24, left: 8, bottom: 6 }}
            barCategoryGap="28%"
            barGap={3}
          >
            <CartesianGrid
              stroke={COLOR_GRID}
              horizontal={false}
              strokeDasharray="3 3"
            />
            <XAxis
              type="number"
              unit="h"
              stroke={COLOR_AXIS}
              tick={{ fill: COLOR_AXIS, fontSize: 10, fontFamily: 'var(--font-mono)' }}
              tickLine={false}
              axisLine={{ stroke: COLOR_GRID }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={96}
              stroke={COLOR_AXIS}
              tick={{ fill: 'rgba(255,255,255,0.78)', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: COLOR_GRID }}
            />
            <Tooltip
              content={<ChartTooltip />}
              cursor={{ fill: 'rgba(84, 120, 255, 0.06)' }}
            />
            <Legend content={() => null} />
            <Bar
              dataKey="planned"
              name="Planned"
              fill={COLOR_PLANNED}
              radius={[0, 6, 6, 0]}
              barSize={14}
            />
            <Bar
              dataKey="actual"
              name="Actual"
              fill={COLOR_ACTUAL}
              radius={[0, 6, 6, 0]}
              barSize={14}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default WeeklyBarChart
