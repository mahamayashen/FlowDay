import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DndContext } from '@dnd-kit/core'
import TaskPool from './TaskPool'
import type { Project } from '../types/project'
import type { Task } from '../types/task'

const projects: Project[] = [
  {
    id: 'proj-1',
    user_id: 'user-1',
    name: 'FlowDay',
    color: '#f59e0b',
    client_name: null,
    hourly_rate: null,
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'proj-2',
    user_id: 'user-1',
    name: 'Client Work',
    color: '#3b82f6',
    client_name: 'ACME',
    hourly_rate: null,
    status: 'active',
    created_at: '2026-01-02T00:00:00Z',
  },
]

const tasks: Task[] = [
  {
    id: 'task-1',
    project_id: 'proj-1',
    title: 'Write docs',
    description: null,
    estimate_minutes: 30,
    priority: 'low',
    status: 'todo',
    due_date: null,
    created_at: '2026-04-18T00:00:00Z',
    completed_at: null,
  },
  {
    id: 'task-2',
    project_id: 'proj-2',
    title: 'Client call',
    description: null,
    estimate_minutes: 60,
    priority: 'high',
    status: 'todo',
    due_date: null,
    created_at: '2026-04-18T00:00:00Z',
    completed_at: null,
  },
]

const tasksByProject: Map<string, Task[]> = new Map([
  ['proj-1', [tasks[0]]],
  ['proj-2', [tasks[1]]],
])

function renderPool(props = { projects, tasksByProject }) {
  return render(
    <DndContext>
      <TaskPool {...props} />
    </DndContext>,
  )
}

describe('TaskPool', () => {
  it('renders the task pool container', () => {
    renderPool()
    expect(screen.getByTestId('task-pool')).toBeInTheDocument()
  })

  it('renders project group headers', () => {
    renderPool()
    expect(screen.getByText('FlowDay')).toBeInTheDocument()
    expect(screen.getByText('Client Work')).toBeInTheDocument()
  })

  it('renders task titles within groups', () => {
    renderPool()
    expect(screen.getByText('Write docs')).toBeInTheDocument()
    expect(screen.getByText('Client call')).toBeInTheDocument()
  })

  it('renders each task with its testid', () => {
    renderPool()
    expect(screen.getByTestId('pool-task-task-1')).toBeInTheDocument()
    expect(screen.getByTestId('pool-task-task-2')).toBeInTheDocument()
  })

  it('renders empty state when no tasks', () => {
    renderPool({ projects, tasksByProject: new Map() })
    expect(screen.getByTestId('task-pool')).toBeInTheDocument()
  })
})
