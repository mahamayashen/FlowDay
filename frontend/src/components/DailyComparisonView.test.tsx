import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import DailyComparisonView from './DailyComparisonView'
import type { TaskComparison } from '../types/analytics'

const tasks: TaskComparison[] = [
  { task_id: 'task-1', task_title: 'Write tests', planned_hours: 1, actual_hours: 0.5, status: 'partial' },
  { task_id: 'task-2', task_title: 'Deploy feature', planned_hours: 2, actual_hours: 2.1, status: 'done' },
  { task_id: 'task-3', task_title: 'Review PR', planned_hours: 0.5, actual_hours: 0, status: 'skipped' },
  { task_id: 'task-4', task_title: 'Hotfix', planned_hours: 0, actual_hours: 1, status: 'unplanned' },
]

describe('DailyComparisonView', () => {
  it('renders a row for each task', () => {
    render(<DailyComparisonView tasks={tasks} />)
    expect(screen.getByText('Write tests')).toBeInTheDocument()
    expect(screen.getByText('Deploy feature')).toBeInTheDocument()
    expect(screen.getByText('Review PR')).toBeInTheDocument()
    expect(screen.getByText('Hotfix')).toBeInTheDocument()
  })

  it('renders planned hours for each task', () => {
    render(<DailyComparisonView tasks={tasks} />)
    expect(screen.getByTestId('planned-task-1')).toHaveTextContent('1.00h')
    expect(screen.getByTestId('planned-task-2')).toHaveTextContent('2.00h')
  })

  it('renders actual hours for each task', () => {
    render(<DailyComparisonView tasks={tasks} />)
    expect(screen.getByTestId('actual-task-1')).toHaveTextContent('0.50h')
    expect(screen.getByTestId('actual-task-2')).toHaveTextContent('2.10h')
  })

  it('renders status badge with correct color for done', () => {
    render(<DailyComparisonView tasks={[tasks[1]]} />)
    const badge = screen.getByTestId('status-badge-task-2')
    expect(badge).toHaveStyle({ backgroundColor: '#22c55e' })
  })

  it('renders status badge with correct color for partial', () => {
    render(<DailyComparisonView tasks={[tasks[0]]} />)
    const badge = screen.getByTestId('status-badge-task-1')
    expect(badge).toHaveStyle({ backgroundColor: '#eab308' })
  })

  it('renders status badge with correct color for skipped', () => {
    render(<DailyComparisonView tasks={[tasks[2]]} />)
    const badge = screen.getByTestId('status-badge-task-3')
    expect(badge).toHaveStyle({ backgroundColor: '#ef4444' })
  })

  it('renders status badge with correct color for unplanned', () => {
    render(<DailyComparisonView tasks={[tasks[3]]} />)
    const badge = screen.getByTestId('status-badge-task-4')
    expect(badge).toHaveStyle({ backgroundColor: '#3b82f6' })
  })

  it('renders empty message when tasks list is empty', () => {
    render(<DailyComparisonView tasks={[]} />)
    expect(screen.getByText('No tasks scheduled')).toBeInTheDocument()
  })
})
