import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useAuthStore } from '../stores/authStore'
import { usePlannerStore } from '../stores/plannerStore'
import type { TokenPair } from '../types/auth'
import type { Project } from '../types/project'
import type { ScheduleBlock } from '../types/scheduleBlock'
import PlannerPage from './PlannerPage'

const mockTokens: TokenPair = {
  access_token: 'access-abc',
  refresh_token: 'refresh-xyz',
  token_type: 'bearer',
}

const mockProjects: Project[] = [
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
]

const mockBlocks: ScheduleBlock[] = []

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

beforeEach(() => {
  useAuthStore.getState().setTokens(mockTokens)
  usePlannerStore.setState({ selectedDate: '2026-04-18', workHoursStart: 8, workHoursEnd: 18 })
  vi.restoreAllMocks()

  vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
    const urlStr = String(url)
    if (urlStr.includes('/projects')) {
      return Promise.resolve(new Response(JSON.stringify(mockProjects), { status: 200 }))
    }
    if (urlStr.includes('/schedule-blocks')) {
      return Promise.resolve(new Response(JSON.stringify(mockBlocks), { status: 200 }))
    }
    return Promise.resolve(new Response('[]', { status: 200 }))
  })
})

describe('PlannerPage', () => {
  it('renders the planner page container', async () => {
    render(<PlannerPage />, { wrapper: createWrapper() })
    expect(screen.getByTestId('page-planner')).toBeInTheDocument()
  })

  it('renders the DateNavigator with the selected date', async () => {
    render(<PlannerPage />, { wrapper: createWrapper() })
    await waitFor(() => expect(screen.getByTestId('selected-date-label')).toBeInTheDocument())
    expect(screen.getByTestId('selected-date-label')).toHaveTextContent('April 18, 2026')
  })

  it('renders the TaskPool sidebar', async () => {
    render(<PlannerPage />, { wrapper: createWrapper() })
    await waitFor(() => expect(screen.getByTestId('task-pool')).toBeInTheDocument())
  })

  it('renders the TimelineGrid', async () => {
    render(<PlannerPage />, { wrapper: createWrapper() })
    await waitFor(() => expect(screen.getByTestId('timeline-grid')).toBeInTheDocument())
  })

  it('navigates to next day when next button is clicked', async () => {
    render(<PlannerPage />, { wrapper: createWrapper() })
    await waitFor(() => expect(screen.getByTestId('next-day-btn')).toBeInTheDocument())
    fireEvent.click(screen.getByTestId('next-day-btn'))
    await waitFor(() =>
      expect(screen.getByTestId('selected-date-label')).toHaveTextContent('April 19, 2026'),
    )
  })
})
