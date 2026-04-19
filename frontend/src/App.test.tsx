import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import App from './App'

const future = { v7_startTransition: true, v7_relativeSplatPath: true } as const

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
        <MemoryRouter initialEntries={['/dashboard']} future={future}>
          <App />
        </MemoryRouter>,
      ),
    ).not.toThrow()
  })
})

describe('Routing', () => {
  it('renders login page at /login', () => {
    render(
      <MemoryRouter initialEntries={['/login']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('renders dashboard page at /dashboard', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-dashboard')).toBeInTheDocument()
  })

  it('renders planner page at /planner', () => {
    render(
      <MemoryRouter initialEntries={['/planner']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-planner')).toBeInTheDocument()
  })

  it('renders review page at /review', () => {
    render(
      <MemoryRouter initialEntries={['/review']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-review')).toBeInTheDocument()
  })

  it('redirects unknown routes to login', () => {
    render(
      <MemoryRouter initialEntries={['/unknown-path']} future={future}>
        <App />
      </MemoryRouter>,
    )
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })
})
