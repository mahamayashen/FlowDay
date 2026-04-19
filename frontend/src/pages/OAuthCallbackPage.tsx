import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom'
import { exchangeOAuthCode, fetchCurrentUser } from '../api/auth'
import { useAuthStore } from '../stores/authStore'

function OAuthCallbackPage(): React.JSX.Element {
  const { provider } = useParams<{ provider: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    const code = searchParams.get('code')
    if (!code || !provider) {
      setError('Missing OAuth code or provider.')
      return
    }

    if (provider !== 'google' && provider !== 'github') {
      setError(`Unknown provider: ${provider}`)
      return
    }

    exchangeOAuthCode(provider, code)
      .then((tokens) => {
        if (controller.signal.aborted) return
        setTokens(tokens)
        return fetchCurrentUser()
      })
      .then((user) => {
        if (controller.signal.aborted || !user) return
        setUser(user)
        navigate('/dashboard', { replace: true })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        const message = err instanceof Error ? err.message : 'Authentication failed.'
        setError(message)
      })

    return () => {
      controller.abort()
    }
  }, [navigate, provider, searchParams, setTokens, setUser])

  if (error) {
    return (
      <main data-testid="oauth-error" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>{error}</p>
        <Link data-testid="link-back-to-login" to="/login">
          Back to Login
        </Link>
      </main>
    )
  }

  return (
    <main data-testid="oauth-loading" style={{ padding: '2rem', textAlign: 'center' }}>
      <p style={{ color: 'var(--text-muted)' }}>Signing you in…</p>
    </main>
  )
}

export default OAuthCallbackPage
