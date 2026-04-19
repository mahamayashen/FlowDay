import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PlannerPage from './pages/PlannerPage'
import ReviewPage from './pages/ReviewPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import ProtectedRoute from './components/ProtectedRoute'
import { useTimerBootstrap } from './hooks/useTimerBootstrap'
import './index.css'

function App(): React.JSX.Element {
  useTimerBootstrap()

  return (
    <div className="dark-bg">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/:provider/callback" element={<OAuthCallbackPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/planner"
          element={
            <ProtectedRoute>
              <PlannerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/review"
          element={
            <ProtectedRoute>
              <ReviewPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  )
}

export default App
