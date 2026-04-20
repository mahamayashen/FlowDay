import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PlannerPage from './pages/PlannerPage'
import ReviewPage from './pages/ReviewPage'
import WeeklyReviewPage from './pages/WeeklyReviewPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import ProtectedRoute from './components/ProtectedRoute'
import NavBar from './components/NavBar'
import { useTimerBootstrap } from './hooks/useTimerBootstrap'
import './index.css'

function AppShell({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <div className="app-layout">
      <NavBar />
      <div className="app-main">{children}</div>
    </div>
  )
}

function App(): React.JSX.Element {
  useTimerBootstrap()

  return (
    <Routes>
      {/* Auth routes — no shell */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />

      {/* Protected app routes — with NavBar shell */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppShell><DashboardPage /></AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/planner"
        element={
          <ProtectedRoute>
            <AppShell><PlannerPage /></AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/review"
        element={
          <ProtectedRoute>
            <AppShell><ReviewPage /></AppShell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/weekly-review"
        element={
          <ProtectedRoute>
            <AppShell><WeeklyReviewPage /></AppShell>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
