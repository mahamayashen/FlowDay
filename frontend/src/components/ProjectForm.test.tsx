import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ProjectForm from './ProjectForm'
import type { Project } from '../types/project'

const mockMutate = vi.fn()

vi.mock('../api/projects', () => ({
  useCreateProject: () => ({ mutate: mockMutate, isPending: false, isError: false, error: null }),
  useUpdateProject: () => ({ mutate: mockMutate, isPending: false, isError: false, error: null }),
}))

const existingProject: Project = {
  id: 'proj-1',
  user_id: 'user-1',
  name: 'Old Name',
  color: '#3b82f6',
  client_name: 'Acme',
  hourly_rate: '150.00',
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
}

beforeEach(() => {
  mockMutate.mockReset()
})

describe('ProjectForm', () => {
  it('renders all fields', () => {
    render(<ProjectForm onSuccess={vi.fn()} />)
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/color/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/client/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/hourly rate/i)).toBeInTheDocument()
  })

  it('submit in create mode calls createProject mutation with payload', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<ProjectForm onSuccess={onSuccess} />)

    await user.clear(screen.getByLabelText(/name/i))
    await user.type(screen.getByLabelText(/name/i), 'New Project')
    await user.clear(screen.getByLabelText(/color/i))
    await user.type(screen.getByLabelText(/color/i), '#f59e0b')

    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'New Project', color: '#f59e0b' }),
        expect.anything(),
      ),
    )
  })

  it('submit in edit mode calls updateProject mutation with id and payload', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<ProjectForm initialData={existingProject} onSuccess={onSuccess} />)

    await user.clear(screen.getByLabelText(/name/i))
    await user.type(screen.getByLabelText(/name/i), 'Updated Name')

    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'proj-1', data: expect.objectContaining({ name: 'Updated Name' }) }),
        expect.anything(),
      ),
    )
  })

  it('pre-fills fields with initialData in edit mode', () => {
    render(<ProjectForm initialData={existingProject} onSuccess={vi.fn()} />)
    expect(screen.getByLabelText<HTMLInputElement>(/name/i).value).toBe('Old Name')
    expect(screen.getByLabelText<HTMLInputElement>(/color/i).value).toBe('#3b82f6')
    expect(screen.getByLabelText<HTMLInputElement>(/client/i).value).toBe('Acme')
    expect(screen.getByLabelText<HTMLInputElement>(/hourly rate/i).value).toBe('150.00')
  })

  it('shows validation error when name is empty', async () => {
    render(<ProjectForm onSuccess={vi.fn()} />)

    // clear the name field and submit
    const nameInput = screen.getByLabelText(/name/i)
    fireEvent.change(nameInput, { target: { value: '' } })
    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(screen.getByTestId('form-error-name')).toBeInTheDocument(),
    )
    expect(mockMutate).not.toHaveBeenCalled()
  })

  it('shows validation error when color is not a valid hex', async () => {
    const user = userEvent.setup()
    render(<ProjectForm onSuccess={vi.fn()} />)

    await user.clear(screen.getByLabelText(/name/i))
    await user.type(screen.getByLabelText(/name/i), 'Test')
    await user.clear(screen.getByLabelText(/color/i))
    await user.type(screen.getByLabelText(/color/i), 'notahex')

    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(screen.getByTestId('form-error-color')).toBeInTheDocument(),
    )
    expect(mockMutate).not.toHaveBeenCalled()
  })
})
