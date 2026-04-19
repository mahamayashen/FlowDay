import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import LoginPage from './LoginPage'

const future = { v7_startTransition: true, v7_relativeSplatPath: true } as const

function renderLogin(): void {
  render(
    <MemoryRouter future={future}>
      <LoginPage />
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  let assignSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    assignSpy = vi.fn()
    vi.stubGlobal('location', { ...window.location, assign: assignSpy })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders a Google sign-in button', () => {
    renderLogin()
    expect(screen.getByTestId('btn-google')).toBeInTheDocument()
  })

  it('renders a GitHub sign-in button', () => {
    renderLogin()
    expect(screen.getByTestId('btn-github')).toBeInTheDocument()
  })

  it('renders the page container', () => {
    renderLogin()
    expect(screen.getByTestId('page-login')).toBeInTheDocument()
  })

  it('Google button navigates to Google OAuth authorize URL', async () => {
    vi.stubEnv('VITE_GOOGLE_CLIENT_ID', 'google-client-123')
    renderLogin()
    await userEvent.click(screen.getByTestId('btn-google'))
    expect(assignSpy).toHaveBeenCalledOnce()
    const url = new URL(assignSpy.mock.calls[0][0])
    expect(url.hostname).toBe('accounts.google.com')
    expect(url.searchParams.get('client_id')).toBe('google-client-123')
    expect(url.searchParams.get('response_type')).toBe('code')
    expect(url.searchParams.get('redirect_uri')).toContain('/auth/google/callback')
    expect(url.searchParams.get('scope')).toMatch(/email/)
  })

  it('GitHub button navigates to GitHub OAuth authorize URL', async () => {
    vi.stubEnv('VITE_GITHUB_CLIENT_ID', 'gh-client-456')
    renderLogin()
    await userEvent.click(screen.getByTestId('btn-github'))
    expect(assignSpy).toHaveBeenCalledOnce()
    const url = new URL(assignSpy.mock.calls[0][0])
    expect(url.hostname).toBe('github.com')
    expect(url.searchParams.get('client_id')).toBe('gh-client-456')
    expect(url.searchParams.get('redirect_uri')).toContain('/auth/github/callback')
  })

  it('Google button is disabled when VITE_GOOGLE_CLIENT_ID is not set', () => {
    vi.stubEnv('VITE_GOOGLE_CLIENT_ID', '')
    renderLogin()
    expect(screen.getByTestId('btn-google')).toBeDisabled()
  })

  it('GitHub button is disabled when VITE_GITHUB_CLIENT_ID is not set', () => {
    vi.stubEnv('VITE_GITHUB_CLIENT_ID', '')
    renderLogin()
    expect(screen.getByTestId('btn-github')).toBeDisabled()
  })
})
