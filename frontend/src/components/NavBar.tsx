import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Lightning,
  CalendarBlank,
  FolderOpen,
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
      end
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

      <NavItem to="/"         icon={<Lightning    size={20} weight="fill" />} label="Today" />
      <NavItem to="/plan"     icon={<CalendarBlank size={20} />}              label="Plan" />
      <NavItem to="/projects" icon={<FolderOpen    size={20} />}              label="Projects" />
      <NavItem to="/review"   icon={<ChartBar      size={20} />}              label="Review" />
      <NavItem to="/weekly"   icon={<Brain         size={20} />}              label="Weekly AI Review" />

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
