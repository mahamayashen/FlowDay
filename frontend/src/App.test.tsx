import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import App from './App'
import { useAuthStore } from './stores/authStore'
import type { TokenPair, User } from './types/auth'

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
}))

function withQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: queryClient }, ui)
}

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

  it('has dark background root element', () => {
    const { container } = render(
      <MemoryRouter future={future}>
        <App />
      </MemoryRouter>,
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toBeTruthy()
    expect(root.className).toContain('dark-bg')
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

  it('redirects /dashboard to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
    expect(screen.queryByTestId('page-dashboard')).not.toBeInTheDocument()
  })

  it('redirects /planner to /login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/planner']} future={future}>
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

  it('renders dashboard page at /dashboard when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-dashboard')).toBeInTheDocument()
  })

  it('renders planner page at /planner when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/planner']} future={future}>
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
})
