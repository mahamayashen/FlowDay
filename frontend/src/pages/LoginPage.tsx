import { useState } from 'react'
import { buildOAuthUrl } from '../utils/oauth'
import './LoginPage.css'

function LoginPage(): React.JSX.Element {
  const [error, setError] = useState<string | null>(null)

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined
  const githubClientId = import.meta.env.VITE_GITHUB_CLIENT_ID as string | undefined

  function handleGoogle(): void {
    try {
      window.location.assign(buildOAuthUrl('google'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to build Google OAuth URL.')
    }
  }

  function handleGitHub(): void {
    try {
      window.location.assign(buildOAuthUrl('github'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to build GitHub OAuth URL.')
    }
  }

  return (
    <main data-testid="page-login" className="login-page">
      <div className="login-card">
        <h1 className="login-title">FlowDay</h1>
        <p className="login-subtitle">Sign in to continue</p>
        {error && (
          <p data-testid="login-error" style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>
            {error}
          </p>
        )}
        <div className="login-buttons">
          <button
            data-testid="btn-google"
            className="login-btn login-btn--google"
            onClick={handleGoogle}
            disabled={!googleClientId}
          >
            Sign in with Google
          </button>
          <button
            data-testid="btn-github"
            className="login-btn login-btn--github"
            onClick={handleGitHub}
            disabled={!githubClientId}
          >
            Sign in with GitHub
          </button>
        </div>
      </div>
    </main>
  )
}

export default LoginPage
