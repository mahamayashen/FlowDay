import './ProjectCard.css'
import type { Project } from '../types/project'

interface ProjectCardProps {
  project: Project
  onClick?: () => void
}

function ProjectCard({ project, onClick }: ProjectCardProps): React.JSX.Element {
  return (
    <div className="project-card" data-testid="project-card" onClick={onClick}>
      <span
        className="project-color-swatch"
        data-testid="project-color-swatch"
        style={{ backgroundColor: project.color }}
      />
      <div className="project-card-body">
        <span className="project-card-name">{project.name}</span>
        {project.client_name && (
          <span className="project-card-client" data-testid="project-client-name">
            {project.client_name}
          </span>
        )}
      </div>
      {project.status === 'archived' && (
        <span className="project-archived-badge">Archived</span>
      )}
    </div>
  )
}

export default ProjectCard
