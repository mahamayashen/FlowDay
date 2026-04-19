import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DndContext } from '@dnd-kit/core'
import TimelineGrid from './TimelineGrid'
import type { ScheduleBlock } from '../types/scheduleBlock'
import type { Task } from '../types/task'
import type { Project } from '../types/project'

const mockTasks: Map<string, Task> = new Map([
  [
    'task-1',
    {
      id: 'task-1',
      project_id: 'proj-1',
      title: 'Write tests',
      description: null,
      estimate_minutes: 60,
      priority: 'medium',
      status: 'todo',
      due_date: null,
      created_at: '2026-04-18T00:00:00Z',
      completed_at: null,
    },
  ],
])

const mockProjects: Map<string, Project> = new Map([
  [
    'proj-1',
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
  ],
])

const defaultProps = {
  workHoursStart: 8,
  workHoursEnd: 12,
  blocks: [] as ScheduleBlock[],
  tasks: mockTasks,
  projects: mockProjects,
  onDropTask: vi.fn(),
  onMoveBlock: vi.fn(),
  onResizeBlock: vi.fn(),
  onDeleteBlock: vi.fn(),
}

function renderWithDnd(props = defaultProps) {
  return render(
    <DndContext>
      <TimelineGrid {...props} />
    </DndContext>,
  )
}

describe('TimelineGrid', () => {
  it('renders hour slots from workHoursStart to workHoursEnd', () => {
    renderWithDnd()
    // 8, 9, 10, 11 (4 slots for 8-12)
    expect(screen.getByTestId('hour-slot-8')).toBeInTheDocument()
    expect(screen.getByTestId('hour-slot-9')).toBeInTheDocument()
    expect(screen.getByTestId('hour-slot-10')).toBeInTheDocument()
    expect(screen.getByTestId('hour-slot-11')).toBeInTheDocument()
  })

  it('does not render a slot for the end hour', () => {
    renderWithDnd()
    expect(screen.queryByTestId('hour-slot-12')).not.toBeInTheDocument()
  })

  it('renders hour labels in AM/PM format', () => {
    renderWithDnd()
    expect(screen.getByText('8:00 AM')).toBeInTheDocument()
    expect(screen.getByText('11:00 AM')).toBeInTheDocument()
  })

  it('renders a schedule block with the task title when blocks are provided', () => {
    const blocks: ScheduleBlock[] = [
      {
        id: 'block-1',
        task_id: 'task-1',
        date: '2026-04-18',
        start_hour: 9,
        end_hour: 10,
        source: 'manual',
        created_at: '2026-04-18T09:00:00Z',
      },
    ]
    renderWithDnd({ ...defaultProps, blocks })
    expect(screen.getByText('Write tests')).toBeInTheDocument()
  })

  it('renders the timeline grid container', () => {
    renderWithDnd()
    expect(screen.getByTestId('timeline-grid')).toBeInTheDocument()
  })
})
