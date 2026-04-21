import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import TodayPage from './pages/TodayPage'
import ProjectsPage from './pages/ProjectsPage'
import PlannerPage from './pages/PlannerPage'
import ReviewPage from './pages/ReviewPage'
import WeeklyReviewPage from './pages/WeeklyReviewPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import NavBar from './components/NavBar'
import './index.css'

// Mock-shell mode: skip auth guard so the redesign is immediately viewable.
// Flip to `false` (or delete this flag) when reconnecting real API.
const MOCK_SHELL = true

function AppShell({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <div className="app-layout">
      <NavBar />
      <div className="app-main">{children}</div>
    </div>
  )
}

function App(): React.JSX.Element {
  // Mock shell: every route renders with the nav shell, no auth check.
  if (MOCK_SHELL) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />

        <Route path="/"         element={<AppShell><TodayPage /></AppShell>} />
        <Route path="/plan"     element={<AppShell><PlannerPage /></AppShell>} />
        <Route path="/projects" element={<AppShell><ProjectsPage /></AppShell>} />
        <Route path="/review"   element={<AppShell><ReviewPage /></AppShell>} />
        <Route path="/weekly"   element={<AppShell><WeeklyReviewPage /></AppShell>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    )
  }

  // Real-auth mode (kept for reference; toggle MOCK_SHELL to re-enable)
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />

      <Route path="/"         element={<AppShell><TodayPage /></AppShell>} />
      <Route path="/plan"     element={<AppShell><PlannerPage /></AppShell>} />
      <Route path="/projects" element={<AppShell><ProjectsPage /></AppShell>} />
      <Route path="/review"   element={<AppShell><ReviewPage /></AppShell>} />
      <Route path="/weekly"   element={<AppShell><WeeklyReviewPage /></AppShell>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
