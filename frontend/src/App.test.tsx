import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    expect(document.body).toBeTruthy()
  })

  it('has dark background root element', () => {
    const { container } = render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toBeTruthy()
    expect(root.className).toContain('dark-bg')
  })

  it('provides QueryClient to the component tree without error', () => {
    // If QueryClientProvider is missing, React Query hooks throw.
    // This test simply asserts the app renders without throwing.
    expect(() =>
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <App />
        </MemoryRouter>,
      ),
    ).not.toThrow()
  })
})

describe('Routing', () => {
  it('renders login page at /login', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('renders dashboard page at /dashboard', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-dashboard')).toBeInTheDocument()
  })

  it('renders planner page at /planner', () => {
    render(
      <MemoryRouter initialEntries={['/planner']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-planner')).toBeInTheDocument()
  })

  it('renders review page at /review', () => {
    render(
      <MemoryRouter initialEntries={['/review']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-review')).toBeInTheDocument()
  })

  it('redirects unknown routes to login', () => {
    render(
      <MemoryRouter initialEntries={['/unknown-path']}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })
})
