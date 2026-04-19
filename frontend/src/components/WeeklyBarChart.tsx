import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import type { WeeklyChartEntry } from '../types/analytics'

interface WeeklyBarChartProps {
  data: WeeklyChartEntry[]
}

function WeeklyBarChart({ data }: WeeklyBarChartProps): React.JSX.Element {
  if (data.length === 0) {
    return <p>No project data for this week</p>
  }

  return (
    <div data-testid="weekly-bar-chart">
      <ul
        aria-label="project list"
        style={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          clip: 'rect(0,0,0,0)',
          whiteSpace: 'nowrap',
        }}
      >
        {data.map((entry) => (
          <li key={entry.name}>{entry.name}</li>
        ))}
      </ul>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={data}>
            <XAxis type="number" unit="h" />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip formatter={(value) => (typeof value === 'number' ? `${value}h` : value)} />
            <Bar dataKey="planned" name="Planned" fill="#f59e0b" />
            <Bar dataKey="actual" name="Actual" fill="#22c55e" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default WeeklyBarChart
