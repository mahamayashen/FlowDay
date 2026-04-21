import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import App from './App'
import { useAuthStore } from './stores/authStore'
import type { TokenPair, User } from './types/auth'

vi.mock('./api/timeEntries', () => ({
  useActiveTimer: () => ({ data: null }),
  useStartTimer: () => ({ mutate: vi.fn() }),
  useStopTimer: () => ({ mutate: vi.fn() }),
}))

vi.mock('./api/projects', () => ({
  useProjects: () => ({ data: [], isLoading: false, isError: false }),
  useCreateProject: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateProject: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteProject: () => ({ mutate: vi.fn() }),
}))

vi.mock('./api/tasks', () => ({
  useProjectTasks: () => ({ data: [], isLoading: false, isError: false }),
  useCreateTask: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateTask: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteTask: () => ({ mutate: vi.fn() }),
  fetchProjectTasks: () => Promise.resolve([]),
  TASK_KEYS: { byProject: (id: string) => ['tasks', id] },
}))

vi.mock('./api/scheduleBlocks', () => ({
  useScheduleBlocks: () => ({ data: [], isLoading: false, isError: false }),
  useCreateScheduleBlock: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateScheduleBlock: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteScheduleBlock: () => ({ mutate: vi.fn() }),
  SCHEDULE_BLOCK_KEYS: { byDate: (d: string) => ['schedule-blocks', d] },
}))

vi.mock('./api/analytics', () => ({
  usePlannedVsActual: () => ({ data: undefined, isLoading: false }),
  useWeeklyStats: () => ({ data: undefined, isLoading: false }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQueries: () => [],
  }
})


const future = { v7_startTransition: true, v7_relativeSplatPath: true } as const

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockUser: User = {
  id: 'usr-1',
  email: 'alice@example.com',
  name: 'Alice',
  settings_json: {},
  created_at: '2026-01-01T00:00:00Z',
}

beforeEach(() => {
  localStorage.clear()
  useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false })
})

describe('App', () => {
  it('renders without crashing', () => {
    render(
      <MemoryRouter future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(document.body).toBeTruthy()
  })

  it('renders the app layout root at an authenticated route', () => {
    useAuthStore.setState({ user: mockUser, tokens: mockTokens, isAuthenticated: true })
    const { container } = render(
      <MemoryRouter initialEntries={['/']} future={future}>
        <App />
      </MemoryRouter>,
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toBeTruthy()
    expect(root.className).toContain('app-layout')
  })

  it('provides QueryClient to the component tree without error', () => {
    expect(() =>
      render(
        <MemoryRouter initialEntries={['/login']} future={future}>
          <App />
        </MemoryRouter>,
      ),
    ).not.toThrow()
  })
})

describe('Routing — unauthenticated', () => {
  it('renders login page at /login', () => {
    render(
      <MemoryRouter initialEntries={['/login']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('redirects / (today) to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
    expect(screen.queryByTestId('page-today')).not.toBeInTheDocument()
  })

  it('redirects /plan to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/plan']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('redirects /review to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/review']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('redirects /projects to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/projects']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('redirects /weekly to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/weekly']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('redirects unknown routes to /login', () => {
    render(
      <MemoryRouter initialEntries={['/unknown-path']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })
})

describe('Routing — authenticated', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: mockUser, tokens: mockTokens, isAuthenticated: true })
  })

  it('renders today page at / when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-today')).toBeInTheDocument()
  })

  it('renders planner page at /plan when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/plan']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-planner')).toBeInTheDocument()
  })

  it('renders review page at /review when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/review']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-review')).toBeInTheDocument()
  })

  it('renders projects page at /projects when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/projects']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-projects')).toBeInTheDocument()
  })

  it('renders weekly review page at /weekly when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/weekly']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-weekly-review')).toBeInTheDocument()
  })
})
