import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  SquaresFour,
  CalendarBlank,
  ChartBar,
  Brain,
  SignOut,
} from '@phosphor-icons/react'
import { useAuthStore } from '../stores/authStore'

interface NavItemProps {
  to: string
  icon: React.ReactNode
  label: string
}

function NavItem({ to, icon, label }: NavItemProps): React.JSX.Element {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
      title={label}
      aria-label={label}
    >
      {icon}
    </NavLink>
  )
}

function NavBar(): React.JSX.Element {
  const logout = useAuthStore((s) => s.logout)

  return (
    <nav className="navbar" aria-label="Main navigation">
      <span className="navbar-logo" aria-label="FlowDay">F</span>

      <NavItem to="/dashboard"     icon={<SquaresFour  size={20} />} label="Dashboard" />
      <NavItem to="/planner"       icon={<CalendarBlank size={20} />} label="Planner" />
      <NavItem to="/review"        icon={<ChartBar      size={20} />} label="Review" />
      <NavItem to="/weekly-review" icon={<Brain         size={20} />} label="AI Weekly Review" />

      <span className="nav-spacer" />

      <button
        className="nav-item"
        onClick={logout}
        title="Sign out"
        aria-label="Sign out"
      >
        <SignOut size={18} />
      </button>
    </nav>
  )
}

export default NavBar
