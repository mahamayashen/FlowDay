import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import WeeklyBarChart from './WeeklyBarChart'
import type { WeeklyChartEntry } from '../types/analytics'

// recharts uses ResizeObserver — stub it for jsdom
vi.stubGlobal('ResizeObserver', class {
  observe() {}
  unobserve() {}
  disconnect() {}
})

const chartData: WeeklyChartEntry[] = [
  { name: 'FlowDay', planned: 10, actual: 8, color: '#f59e0b' },
  { name: 'Backend', planned: 5, actual: 6, color: '#3b82f6' },
]

describe('WeeklyBarChart', () => {
  it('renders the chart wrapper', () => {
    render(<WeeklyBarChart data={chartData} />)
    expect(screen.getByTestId('weekly-bar-chart')).toBeInTheDocument()
  })

  it('renders project names as Y-axis labels', () => {
    render(<WeeklyBarChart data={chartData} />)
    expect(screen.getByText('FlowDay')).toBeInTheDocument()
    expect(screen.getByText('Backend')).toBeInTheDocument()
  })

  it('renders empty state when data is empty', () => {
    render(<WeeklyBarChart data={[]} />)
    expect(screen.getByText('No project data for this week')).toBeInTheDocument()
  })
})
