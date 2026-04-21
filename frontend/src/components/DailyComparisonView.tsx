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
import type { TaskComparison } from '../types/analytics'
import { statusTagColor } from '../utils/reviewUtils'
import './DailyComparisonView.css'

interface DailyComparisonViewProps {
  tasks: TaskComparison[]
}

const COLOR_PLANNED = '#5478FF'
const COLOR_ACTUAL = '#FFDE42'
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
    <div className="daily-tooltip">
      <div className="daily-tooltip-label">{label}</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="daily-tooltip-row">
          <span className="daily-tooltip-dot" style={{ background: entry.color }} />
          <span className="daily-tooltip-key">{entry.name}</span>
          <span className="daily-tooltip-value">
            {typeof entry.value === 'number' ? `${entry.value.toFixed(2)}h` : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

function DailyComparisonView({ tasks }: DailyComparisonViewProps): React.JSX.Element {
  if (tasks.length === 0) {
    return <p className="daily-empty">No tasks scheduled</p>
  }

  // Shorten long task titles for the X-axis without losing meaning in the list below
  const chartData = tasks.map((t) => ({
    name: t.task_title.length > 18 ? t.task_title.slice(0, 17) + '…' : t.task_title,
    planned: Math.round(t.planned_hours * 100) / 100,
    actual: Math.round(t.actual_hours * 100) / 100,
  }))

  return (
    <div className="daily-comparison">
      {/* Line chart — overview */}
      <div className="daily-chart-card" aria-hidden="true">
        <div className="daily-legend">
          <span className="daily-legend-item">
            <span className="daily-legend-dot" style={{ background: COLOR_PLANNED }} />
            Planned
          </span>
          <span className="daily-legend-item">
            <span className="daily-legend-dot" style={{ background: COLOR_ACTUAL }} />
            Actual
          </span>
        </div>
        <div className="daily-chart-canvas">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 12, right: 18, left: 0, bottom: 4 }}
            >
              <CartesianGrid stroke={COLOR_GRID} strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                stroke={COLOR_AXIS}
                tick={{ fill: COLOR_AXIS, fontSize: 10, fontFamily: 'var(--font-mono)' }}
                tickLine={false}
                axisLine={{ stroke: COLOR_GRID }}
                interval={0}
              />
              <YAxis
                unit="h"
                stroke={COLOR_AXIS}
                tick={{ fill: COLOR_AXIS, fontSize: 10, fontFamily: 'var(--font-mono)' }}
                tickLine={false}
                axisLine={{ stroke: COLOR_GRID }}
                allowDecimals={false}
              />
              <Tooltip
                content={<ChartTooltip />}
                cursor={{ stroke: 'rgba(84, 120, 255, 0.3)', strokeWidth: 1 }}
              />
              <Line
                type="monotone"
                dataKey="planned"
                name="Planned"
                stroke={COLOR_PLANNED}
                strokeWidth={2}
                dot={{ r: 3.5, fill: COLOR_PLANNED, strokeWidth: 0 }}
                activeDot={{ r: 5.5, fill: COLOR_PLANNED, stroke: '#0a0e1a', strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual"
                stroke={COLOR_ACTUAL}
                strokeWidth={2}
                dot={{ r: 3.5, fill: COLOR_ACTUAL, strokeWidth: 0 }}
                activeDot={{ r: 5.5, fill: COLOR_ACTUAL, stroke: '#0a0e1a', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Per-task detail rows */}
      <ul className="daily-task-list">
        {tasks.map((task) => {
          const delta = task.actual_hours - task.planned_hours
          const deltaSign = delta > 0.01 ? '+' : delta < -0.01 ? '−' : '±'
          const deltaAbs = Math.abs(delta).toFixed(2)
          return (
            <li key={task.task_id} className="daily-task-row">
              <span className="daily-task-title">{task.task_title}</span>
              <span className="daily-task-metrics">
                <span className="daily-metric daily-metric--planned">
                  <span className="daily-metric-label">P</span>
                  <span data-testid={`planned-${task.task_id}`} className="daily-metric-value">
                    {task.planned_hours.toFixed(2)}h
                  </span>
                </span>
                <span className="daily-metric daily-metric--actual">
                  <span className="daily-metric-label">A</span>
                  <span data-testid={`actual-${task.task_id}`} className="daily-metric-value">
                    {task.actual_hours.toFixed(2)}h
                  </span>
                </span>
                <span className="daily-metric-delta">
                  {deltaSign}
                  {deltaAbs}h
                </span>
              </span>
              <span
                data-testid={`status-badge-${task.task_id}`}
                className="daily-status-badge"
                style={{ backgroundColor: statusTagColor(task.status) }}
              >
                {task.status}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default DailyComparisonView
