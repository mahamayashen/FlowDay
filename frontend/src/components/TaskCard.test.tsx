import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import TaskCard from './TaskCard'
import type { Task } from '../types/task'

// Stub out the timer API so TaskCard tests stay focused on card rendering
vi.mock('../api/timeEntries', () => ({
  useActiveTimer: () => ({ data: null }),
  useStartTimer: () => ({ mutate: vi.fn() }),
  useStopTimer: () => ({ mutate: vi.fn() }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

function renderCard(task: Task) {
  return render(<TaskCard task={task} />, { wrapper })
}

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
    renderCard(baseTask)
    expect(screen.getByText('Write unit tests')).toBeInTheDocument()
  })

  it('renders priority indicator with correct class', () => {
    renderCard(baseTask)
    const indicator = screen.getByTestId('task-priority-indicator')
    expect(indicator).toHaveClass('priority-high')
  })

  it('renders priority indicator for each priority level', () => {
    const priorities = ['low', 'medium', 'high', 'urgent'] as const
    for (const priority of priorities) {
      const { unmount } = renderCard({ ...baseTask, priority })
      const indicator = screen.getByTestId('task-priority-indicator')
      expect(indicator).toHaveClass(`priority-${priority}`)
      unmount()
    }
  })

  it('renders status badge with correct text', () => {
    renderCard(baseTask)
    expect(screen.getByTestId('task-status-badge')).toHaveTextContent('Todo')
  })

  it('renders status badge for in_progress', () => {
    renderCard({ ...baseTask, status: 'in_progress' })
    expect(screen.getByTestId('task-status-badge')).toHaveTextContent('In Progress')
  })

  it('renders status badge for done', () => {
    renderCard({ ...baseTask, status: 'done' })
    expect(screen.getByTestId('task-status-badge')).toHaveTextContent('Done')
  })

  it('renders due date when present', () => {
    renderCard({ ...baseTask, due_date: '2026-04-30' })
    expect(screen.getByTestId('task-due-date')).toBeInTheDocument()
    expect(screen.getByTestId('task-due-date').textContent).toContain('2026-04-30')
  })

  it('does not render due date when absent', () => {
    renderCard(baseTask)
    expect(screen.queryByTestId('task-due-date')).not.toBeInTheDocument()
  })

  it('adds overdue class when due date is in the past', () => {
    renderCard({ ...baseTask, due_date: '2020-01-01' })
    expect(screen.getByTestId('task-due-date')).toHaveClass('overdue')
  })

  it('does not add overdue class when due date is in the future', () => {
    renderCard({ ...baseTask, due_date: '2099-12-31' })
    expect(screen.getByTestId('task-due-date')).not.toHaveClass('overdue')
  })

  it('renders timer start button when no active timer for this task', () => {
    renderCard(baseTask)
    expect(screen.getByTestId('timer-start-btn')).toBeInTheDocument()
  })
})
