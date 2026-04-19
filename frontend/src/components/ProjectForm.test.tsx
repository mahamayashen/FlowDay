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
    expect(screen.getByLabelText('Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Color')).toBeInTheDocument()
    expect(screen.getByLabelText('Client name')).toBeInTheDocument()
    expect(screen.getByLabelText('Hourly rate')).toBeInTheDocument()
  })

  it('submit in create mode calls createProject mutation with payload', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<ProjectForm onSuccess={onSuccess} />)

    await user.clear(screen.getByLabelText('Name'))
    await user.type(screen.getByLabelText('Name'), 'New Project')
    await user.clear(screen.getByLabelText('Color'))
    await user.type(screen.getByLabelText('Color'), '#f59e0b')

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

    await user.clear(screen.getByLabelText('Name'))
    await user.type(screen.getByLabelText('Name'), 'Updated Name')

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
    expect(screen.getByLabelText<HTMLInputElement>('Name').value).toBe('Old Name')
    expect(screen.getByLabelText<HTMLInputElement>('Color').value).toBe('#3b82f6')
    expect(screen.getByLabelText<HTMLInputElement>('Client name').value).toBe('Acme')
    expect(screen.getByLabelText<HTMLInputElement>('Hourly rate').value).toBe('150.00')
  })

  it('shows validation error when name is empty', async () => {
    render(<ProjectForm onSuccess={vi.fn()} />)

    const nameInput = screen.getByLabelText('Name')
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

    await user.clear(screen.getByLabelText('Name'))
    await user.type(screen.getByLabelText('Name'), 'Test')
    await user.clear(screen.getByLabelText('Color'))
    await user.type(screen.getByLabelText('Color'), 'notahex')

    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() =>
      expect(screen.getByTestId('form-error-color')).toBeInTheDocument(),
    )
    expect(mockMutate).not.toHaveBeenCalled()
  })
})
