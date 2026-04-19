import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaskForm from './TaskForm'
import type { Task } from '../types/task'

const mockMutate = vi.fn()

vi.mock('../api/tasks', () => ({
  useCreateTask: () => ({ mutate: mockMutate, isPending: false }),
  useUpdateTask: () => ({ mutate: mockMutate, isPending: false }),
}))

const existingTask: Task = {
  id: 'task-1',
  project_id: 'proj-1',
  title: 'Old Title',
  description: 'Some description',
  estimate_minutes: 60,
  priority: 'high',
  status: 'in_progress',
  due_date: '2026-05-01',
  created_at: '2026-01-01T00:00:00Z',
  completed_at: null,
}

beforeEach(() => {
  mockMutate.mockReset()
})

describe('TaskForm', () => {
  it('renders all fields', () => {
    render(<TaskForm projectId="proj-1" onSuccess={vi.fn()} />)
    expect(screen.getByLabelText('Title')).toBeInTheDocument()
    expect(screen.getByLabelText('Estimate (minutes)')).toBeInTheDocument()
    expect(screen.getByLabelText('Priority')).toBeInTheDocument()
    expect(screen.getByLabelText('Status')).toBeInTheDocument()
    expect(screen.getByLabelText('Due date')).toBeInTheDocument()
  })

  it('submit in create mode calls createTask mutation with projectId and payload', async () => {
    const user = userEvent.setup()
    render(<TaskForm projectId="proj-1" onSuccess={vi.fn()} />)

    await user.type(screen.getByLabelText('Title'), 'New Task')
    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          projectId: 'proj-1',
          data: expect.objectContaining({ title: 'New Task' }),
        }),
        expect.anything(),
      ),
    )
  })

  it('submit in edit mode calls updateTask mutation with projectId, taskId and payload', async () => {
    const user = userEvent.setup()
    render(<TaskForm projectId="proj-1" initialData={existingTask} onSuccess={vi.fn()} />)

    await user.clear(screen.getByLabelText('Title'))
    await user.type(screen.getByLabelText('Title'), 'Updated Title')
    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          projectId: 'proj-1',
          taskId: 'task-1',
          data: expect.objectContaining({ title: 'Updated Title' }),
        }),
        expect.anything(),
      ),
    )
  })

  it('pre-fills fields with initialData in edit mode', () => {
    render(<TaskForm projectId="proj-1" initialData={existingTask} onSuccess={vi.fn()} />)
    expect(screen.getByLabelText<HTMLInputElement>('Title').value).toBe('Old Title')
    expect(screen.getByLabelText<HTMLInputElement>('Estimate (minutes)').value).toBe('60')
    expect(screen.getByLabelText<HTMLSelectElement>('Priority').value).toBe('high')
    expect(screen.getByLabelText<HTMLSelectElement>('Status').value).toBe('in_progress')
    expect(screen.getByLabelText<HTMLInputElement>('Due date').value).toBe('2026-05-01')
  })

  it('shows validation error when title is empty', async () => {
    render(<TaskForm projectId="proj-1" onSuccess={vi.fn()} />)
    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(screen.getByTestId('form-error-title')).toBeInTheDocument(),
    )
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('shows validation error when estimate is negative', async () => {
    const user = userEvent.setup()
    render(<TaskForm projectId="proj-1" onSuccess={vi.fn()} />)

    await user.type(screen.getByLabelText('Title'), 'Test')
    fireEvent.change(screen.getByLabelText('Estimate (minutes)'), { target: { value: '-5' } })
    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(screen.getByTestId('form-error-estimate')).toBeInTheDocument(),
    )
    expect(mockMutate).not.toHaveBeenCalled()
  })
})
