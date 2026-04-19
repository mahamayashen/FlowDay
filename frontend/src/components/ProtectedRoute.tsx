import { useEffect, useRef } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { fetchCurrentUser, AuthError } from '../api/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps): React.JSX.Element {
  const { isAuthenticated, tokens, user, setUser, setUserLoading, logout } = useAuthStore()
  const navigate = useNavigate()
  const fetchingRef = useRef(false)

  useEffect(() => {
    if (tokens && !user && !fetchingRef.current) {
      fetchingRef.current = true
      setUserLoading(true)
      fetchCurrentUser()
        .then(setUser)
        .catch((err: unknown) => {
          if (err instanceof AuthError && err.status >= 500) {
            // Server error — don't destroy the session, just stop loading
            setUserLoading(false)
          } else {
            logout()
            navigate('/login', { replace: true })
          }
        })
        .finally(() => {
          fetchingRef.current = false
        })
    }
    return () => {
      if (fetchingRef.current) {
        fetchingRef.current = false
        setUserLoading(false)
      }
    }
  }, [tokens, user, setUser, setUserLoading, logout, navigate])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (tokens && !user) {
    return <div data-testid="auth-loading" />
  }

  return <>{children}</>
}

export default ProtectedRoute
