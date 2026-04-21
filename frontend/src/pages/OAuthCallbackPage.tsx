import { useEffect, useRef, useState } from 'react'
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom'
import { exchangeOAuthCode, fetchCurrentUser } from '../api/auth'
import { useAuthStore } from '../stores/authStore'

function OAuthCallbackPage(): React.JSX.Element {
  const { provider } = useParams<{ provider: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setTokens, setUser } = useAuthStore()
  const [error, setError] = useState<string | null>(null)
  const exchangedRef = useRef(false)

  useEffect(() => {
    // Guard against StrictMode double-execution — OAuth codes are single-use
    if (exchangedRef.current) return
    exchangedRef.current = true

    const code = searchParams.get('code')
    if (!code || !provider) {
      setError('Missing OAuth code or provider.')
      return
    }

    if (provider !== 'google' && provider !== 'github') {
      setError(`Unknown provider: ${provider}`)
      return
    }

    const urlState = searchParams.get('state')
    const storedState = sessionStorage.getItem('oauth_state')
    if (urlState && storedState && urlState === storedState) {
      sessionStorage.removeItem('oauth_state')
    }

    exchangeOAuthCode(provider, code)
      .then((tokens) => {
        console.log('[OAuth] tokens received', tokens)
        setTokens(tokens)
        return fetchCurrentUser()
      })
      .then((user) => {
        console.log('[OAuth] user received', user)
        if (!user) return
        setUser(user)
        navigate('/dashboard', { replace: true })
      })
      .catch((err: unknown) => {
        console.error('[OAuth] error', err)
        const message = err instanceof Error ? err.message : 'Authentication failed.'
        setError(message)
      })
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
