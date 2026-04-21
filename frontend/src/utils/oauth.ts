export function buildOAuthUrl(provider: 'google' | 'github'): string {
  const origin = window.location.origin
  const redirectUri = `${origin}/auth/${provider}/callback`

  const state = crypto.randomUUID()
  localStorage.setItem('oauth_state', state)

  if (provider === 'google') {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    if (!clientId) throw new Error('VITE_GOOGLE_CLIENT_ID is not set')
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'email profile',
      state,
    })
    return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
  }

  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
  if (!clientId) throw new Error('VITE_GITHUB_CLIENT_ID is not set')
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: 'user:email',
    state,
  })
  return `https://github.com/login/oauth/authorize?${params.toString()}`
}
