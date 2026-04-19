import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProjectCard from './ProjectCard'
import type { Project } from '../types/project'

const baseProject: Project = {
  id: 'proj-1',
  user_id: 'user-1',
  name: 'My Project',
  color: '#f59e0b',
  client_name: null,
  hourly_rate: null,
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
}

describe('ProjectCard', () => {
  it('renders project name', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.getByText('My Project')).toBeInTheDocument()
  })

  it('renders color swatch with correct background color', () => {
    render(<ProjectCard project={baseProject} />)
    const swatch = screen.getByTestId('project-color-swatch')
    expect(swatch).toHaveStyle({ backgroundColor: '#f59e0b' })
  })

  it('renders client name when present', () => {
    const project = { ...baseProject, client_name: 'Acme Corp' }
    render(<ProjectCard project={project} />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('does not render client name when absent', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.queryByTestId('project-client-name')).not.toBeInTheDocument()
  })

  it('renders archived badge when status is archived', () => {
    const project = { ...baseProject, status: 'archived' as const }
    render(<ProjectCard project={project} />)
    expect(screen.getByText('Archived')).toBeInTheDocument()
  })

  it('does not render archived badge for active projects', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.queryByText('Archived')).not.toBeInTheDocument()
  })
})
