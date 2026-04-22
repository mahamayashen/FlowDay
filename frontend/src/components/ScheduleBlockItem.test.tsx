import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DndContext } from '@dnd-kit/core'
import ScheduleBlockItem from './ScheduleBlockItem'
import type { ScheduleBlock } from '../types/scheduleBlock'
import type { Task } from '../types/task'

const mockTask: Task = {
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
}

const manualBlock: ScheduleBlock = {
  id: 'block-1',
  task_id: 'task-1',
  date: '2026-04-18',
  start_hour: 9,
  end_hour: 10,
  source: 'manual',
  created_at: '2026-04-18T09:00:00Z',
}

const calendarBlock: ScheduleBlock = {
  id: 'block-2',
  task_id: 'task-2',
  date: '2026-04-18',
  start_hour: 14,
  end_hour: 15,
  source: 'google_calendar',
  created_at: '2026-04-18T14:00:00Z',
}

const defaultStyle = { top: 60, height: 60 }

function renderBlock(block: ScheduleBlock, task: Task | undefined = mockTask, extra = {}) {
  return render(
    <DndContext>
      <ScheduleBlockItem
        block={block}
        task={task}
        projectColor="#f59e0b"
        style={defaultStyle}
        workHoursEnd={18}
        onDelete={vi.fn()}
        onResizeBlock={vi.fn()}
        {...extra}
      />
    </DndContext>,
  )
}

describe('ScheduleBlockItem — manual block', () => {
  it('renders with testid schedule-block', () => {
    renderBlock(manualBlock)
    expect(screen.getByTestId('schedule-block')).toBeInTheDocument()
  })

  it('displays the task title', () => {
    renderBlock(manualBlock)
    expect(screen.getByText('Write tests')).toBeInTheDocument()
  })

  it('renders a delete button', () => {
    renderBlock(manualBlock)
    expect(screen.getByTestId('delete-block-btn')).toBeInTheDocument()
  })

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = vi.fn()
    renderBlock(manualBlock, mockTask, { onDelete })
    fireEvent.click(screen.getByTestId('delete-block-btn'))
    expect(onDelete).toHaveBeenCalledWith('block-1')
  })

  // Regression: the delete button lives inside a dnd-kit draggable. Without
  // stopping propagation on pointerdown, any slight jitter between pointerdown
  // and click starts a drag and the click is swallowed, so users can't delete.
  // dnd-kit's listeners are React-level props, so we test React-level
  // propagation via a wrapping onPointerDown handler.
  it('does not propagate pointerdown to the React-level parent', () => {
    const parentHandler = vi.fn()
    render(
      <DndContext>
        <div onPointerDown={parentHandler}>
          <ScheduleBlockItem
            block={manualBlock}
            task={mockTask}
            projectColor="#f59e0b"
            style={defaultStyle}
            workHoursEnd={18}
            onDelete={vi.fn()}
            onResizeBlock={vi.fn()}
          />
        </div>
      </DndContext>,
    )

    fireEvent.pointerDown(screen.getByTestId('delete-block-btn'))

    expect(parentHandler).not.toHaveBeenCalled()
  })

  it('renders a resize handle', () => {
    renderBlock(manualBlock)
    expect(screen.getByTestId('resize-handle')).toBeInTheDocument()
  })
})

describe('ScheduleBlockItem — calendar block', () => {
  it('renders with testid calendar-block', () => {
    renderBlock(calendarBlock, undefined)
    expect(screen.getByTestId('calendar-block')).toBeInTheDocument()
  })

  it('does NOT render a delete button', () => {
    renderBlock(calendarBlock, undefined)
    expect(screen.queryByTestId('delete-block-btn')).not.toBeInTheDocument()
  })

  it('does NOT render a resize handle', () => {
    renderBlock(calendarBlock, undefined)
    expect(screen.queryByTestId('resize-handle')).not.toBeInTheDocument()
  })

  it('has the calendar CSS class', () => {
    renderBlock(calendarBlock, undefined)
    expect(screen.getByTestId('calendar-block')).toHaveClass('calendar')
  })
})

describe('ScheduleBlockItem — resize', () => {
  it('calls onResizeBlock when resize handle is used', () => {
    const onResizeBlock = vi.fn()
    renderBlock(manualBlock, mockTask, { onResizeBlock })

    const handle = screen.getByTestId('resize-handle')
    fireEvent.pointerDown(handle, { clientY: 100 })
    fireEvent.pointerMove(handle, { clientY: 160 })
    fireEvent.pointerUp(handle, { clientY: 160 })

    expect(onResizeBlock).toHaveBeenCalledWith('block-1', expect.any(Number))
  })
})
