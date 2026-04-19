import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TaskCard from './TaskCard'
import type { Task } from '../types/task'

const baseTask: Task = {
  id: 'task-1',
  project_id: 'proj-1',
  title: 'Write unit tests',
  description: null,
  estimate_minutes: 90,
  priority: 'high',
  status: 'todo',
  due_date: null,
  created_at: '2026-01-01T00:00:00Z',
  completed_at: null,
}

describe('TaskCard', () => {
  it('renders task title', () => {
    render(<TaskCard task={baseTask} />)
    expect(screen.getByText('Write unit tests')).toBeInTheDocument()
  })

  it('renders priority indicator with correct class', () => {
    render(<TaskCard task={baseTask} />)
    const indicator = screen.getByTestId('task-priority-indicator')
    expect(indicator).toHaveClass('priority-high')
  })

  it('renders priority indicator for each priority level', () => {
    const priorities = ['low', 'medium', 'high', 'urgent'] as const
    for (const priority of priorities) {
      const { unmount } = render(<TaskCard task={{ ...baseTask, priority }} />)
      const indicator = screen.getByTestId('task-priority-indicator')
      expect(indicator).toHaveClass(`priority-${priority}`)
      unmount()
    }
  })

  it('renders status badge with correct text', () => {
    render(<TaskCard task={baseTask} />)
    expect(screen.getByTestId('task-status-badge')).toHaveTextContent('Todo')
  })

  it('renders status badge for in_progress', () => {
    render(<TaskCard task={{ ...baseTask, status: 'in_progress' }} />)
    expect(screen.getByTestId('task-status-badge')).toHaveTextContent('In Progress')
  })

  it('renders status badge for done', () => {
    render(<TaskCard task={{ ...baseTask, status: 'done' }} />)
    expect(screen.getByTestId('task-status-badge')).toHaveTextContent('Done')
  })

  it('renders due date when present', () => {
    render(<TaskCard task={{ ...baseTask, due_date: '2026-04-30' }} />)
    expect(screen.getByTestId('task-due-date')).toBeInTheDocument()
    expect(screen.getByTestId('task-due-date').textContent).toContain('2026-04-30')
  })

  it('does not render due date when absent', () => {
    render(<TaskCard task={baseTask} />)
    expect(screen.queryByTestId('task-due-date')).not.toBeInTheDocument()
  })

  it('adds overdue class when due date is in the past', () => {
    render(<TaskCard task={{ ...baseTask, due_date: '2020-01-01' }} />)
    expect(screen.getByTestId('task-due-date')).toHaveClass('overdue')
  })

  it('does not add overdue class when due date is in the future', () => {
    render(<TaskCard task={{ ...baseTask, due_date: '2099-12-31' }} />)
    expect(screen.getByTestId('task-due-date')).not.toHaveClass('overdue')
  })
})
