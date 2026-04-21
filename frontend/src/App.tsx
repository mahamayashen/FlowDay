import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import TodayPage from './pages/TodayPage'
import ProjectsPage from './pages/ProjectsPage'
import PlannerPage from './pages/PlannerPage'
import ReviewPage from './pages/ReviewPage'
import WeeklyReviewPage from './pages/WeeklyReviewPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import NavBar from './components/NavBar'
import { useAuthStore } from './stores/authStore'
import './index.css'

function AppShell({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <div className="app-layout">
      <NavBar />
      <div className="app-main">{children}</div>
    </div>
  )
}

function RequireAuth({ children }: { children: React.ReactNode }): React.JSX.Element {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <AppShell>{children}</AppShell>
}

function App(): React.JSX.Element {
  const hydrate = useAuthStore((s) => s.hydrate)

  // Rehydrate tokens from localStorage on mount so a page reload doesn't
  // kick the user back to /login while they still have a valid refresh token.
  useEffect(() => {
    hydrate()
  }, [hydrate])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />

      <Route path="/"         element={<RequireAuth><TodayPage /></RequireAuth>} />
      <Route path="/plan"     element={<RequireAuth><PlannerPage /></RequireAuth>} />
      <Route path="/projects" element={<RequireAuth><ProjectsPage /></RequireAuth>} />
      <Route path="/review"   element={<RequireAuth><ReviewPage /></RequireAuth>} />
      <Route path="/weekly"   element={<RequireAuth><WeeklyReviewPage /></RequireAuth>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
