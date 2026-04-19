import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DashboardPage from './DashboardPage'
import type { Project } from '../types/project'
import type { Task } from '../types/task'

const mockProjects: Project[] = [
  {
    id: 'proj-1',
    user_id: 'user-1',
    name: 'Alpha Project',
    color: '#f59e0b',
    client_name: null,
    hourly_rate: null,
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'proj-2',
    user_id: 'user-1',
    name: 'Beta Project',
    color: '#3b82f6',
    client_name: 'Acme',
    hourly_rate: null,
    status: 'active',
    created_at: '2026-01-02T00:00:00Z',
  },
]

const mockTasks: Task[] = [
  {
    id: 'task-1',
    project_id: 'proj-1',
    title: 'Write tests',
    description: null,
    estimate_minutes: 60,
    priority: 'high',
    status: 'todo',
    due_date: null,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: null,
  },
  {
    id: 'task-2',
    project_id: 'proj-1',
    title: 'Deploy app',
    description: null,
    estimate_minutes: 30,
    priority: 'urgent',
    status: 'in_progress',
    due_date: '2026-05-01',
    created_at: '2026-01-02T00:00:00Z',
    completed_at: null,
  },
]

vi.mock('../api/projects', () => ({
  useProjects: vi.fn(),
  useCreateProject: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateProject: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteProject: () => ({ mutate: vi.fn() }),
}))

vi.mock('../api/tasks', () => ({
  useProjectTasks: vi.fn(),
  useCreateTask: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateTask: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteTask: () => ({ mutate: vi.fn() }),
}))

import { useProjects } from '../api/projects'
import { useProjectTasks } from '../api/tasks'

const mockUseProjects = vi.mocked(useProjects)
const mockUseProjectTasks = vi.mocked(useProjectTasks)

beforeEach(() => {
  mockUseProjects.mockReturnValue({
    data: mockProjects,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useProjects>)

  mockUseProjectTasks.mockReturnValue({
    data: mockTasks,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useProjectTasks>)
})

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

describe('DashboardPage', () => {
  it('renders project list with project names', () => {
    renderDashboard()
    expect(screen.getByText('Alpha Project')).toBeInTheDocument()
    expect(screen.getByText('Beta Project')).toBeInTheDocument()
  })

  it('renders New Project button', () => {
    renderDashboard()
    expect(screen.getByTestId('btn-new-project')).toBeInTheDocument()
  })

  it('shows project form when New Project is clicked', () => {
    renderDashboard()
    fireEvent.click(screen.getByTestId('btn-new-project'))
    expect(screen.getByTestId('project-form-panel')).toBeInTheDocument()
  })

  it('shows task list after selecting a project', () => {
    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    expect(screen.getByText('Write tests')).toBeInTheDocument()
    expect(screen.getByText('Deploy app')).toBeInTheDocument()
  })

  it('shows New Task button after selecting a project', () => {
    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    expect(screen.getByTestId('btn-new-task')).toBeInTheDocument()
  })

  it('shows task form when New Task is clicked', () => {
    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    fireEvent.click(screen.getByTestId('btn-new-task'))
    expect(screen.getByTestId('task-form-panel')).toBeInTheDocument()
  })

  it('shows loading indicator while projects are loading', () => {
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useProjects>)

    renderDashboard()
    expect(screen.getByTestId('projects-loading')).toBeInTheDocument()
  })

  it('shows task filter controls after selecting a project', () => {
    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    expect(screen.getByTestId('task-filter')).toBeInTheDocument()
  })

  it('shows project edit form when edit button is clicked', () => {
    renderDashboard()
    fireEvent.click(screen.getAllByTestId('btn-edit-project')[0])
    expect(screen.getByTestId('project-form-panel')).toBeInTheDocument()
  })

  it('shows task edit form when task edit button is clicked', () => {
    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    fireEvent.click(screen.getAllByTestId('btn-edit-task')[0])
    expect(screen.getByTestId('task-form-panel')).toBeInTheDocument()
  })

  it('shows error message when projects fail to load', () => {
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useProjects>)

    renderDashboard()
    expect(screen.getByTestId('projects-error')).toBeInTheDocument()
  })

  it('shows error message when tasks fail to load', () => {
    mockUseProjectTasks.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useProjectTasks>)

    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    expect(screen.getByTestId('tasks-error')).toBeInTheDocument()
    expect(screen.queryByTestId('task-filter')).not.toBeInTheDocument()
  })

  it('shows loading indicator while tasks are loading', () => {
    mockUseProjectTasks.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useProjectTasks>)

    renderDashboard()
    fireEvent.click(screen.getAllByTestId('project-card')[0])
    expect(screen.getByTestId('tasks-loading')).toBeInTheDocument()
  })
})
