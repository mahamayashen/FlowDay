import { useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { fetchCurrentUser } from '../api/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps): React.JSX.Element {
  const { isAuthenticated, tokens, user, setUser, setUserLoading, isUserLoading, logout } =
    useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (tokens && !user && !isUserLoading) {
      setUserLoading(true)
      fetchCurrentUser()
        .then(setUser)
        .catch(() => {
          logout()
          navigate('/login', { replace: true })
        })
    }
  }, [tokens, user, isUserLoading, setUser, setUserLoading, logout, navigate])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (tokens && !user) {
    return <div data-testid="auth-loading" />
  }

  return <>{children}</>
}

export default ProtectedRoute
