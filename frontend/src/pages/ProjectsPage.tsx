import { useState, useEffect } from 'react'
import { Plus, FolderOpen, Clock, Flag } from '@phosphor-icons/react'
import { useProjects } from '../api/projects'
import { useProjectTasks } from '../api/tasks'
import TaskCard from '../components/TaskCard'
import type { Project } from '../types/project'
import './ProjectsPage.css'

function ProjectsPage(): React.JSX.Element {
  const { data: projects = [], isLoading: projectsLoading } = useProjects()
  const [selectedId, setSelectedId] = useState<string>('')

  // Select the first project once the list lands.
  useEffect(() => {
    if (!selectedId && projects.length > 0) {
      setSelectedId(projects[0].id)
    }
  }, [projects, selectedId])

  const { data: tasks = [], isLoading: tasksLoading } = useProjectTasks(selectedId)
  const selected: Project | undefined = projects.find((p) => p.id === selectedId)

  const totalEstimateHours =
    tasks.reduce((s, t) => s + (t.estimate_minutes ?? 0), 0) / 60
  const urgentCount = tasks.filter(
    (t) => t.priority === 'urgent' || t.priority === 'high',
  ).length

  return (
    <main className="projects-page" data-testid="page-projects">
      <aside className="projects-sidebar">
        <div className="projects-sidebar-head">
          <h2 className="projects-sidebar-title">Projects</h2>
          <button className="btn-ghost" aria-label="Create project">
            <Plus size={16} weight="bold" />
          </button>
        </div>

        {projectsLoading ? (
          <p className="projects-loading">Loading…</p>
        ) : projects.length === 0 ? (
          <p className="projects-empty">
            No projects yet. Create one to get started.
          </p>
        ) : (
          <ul className="projects-list">
            {projects.map((p) => {
              const active = p.id === selectedId
              return (
                <li key={p.id}>
                  <button
                    className={`project-row${active ? ' project-row--active' : ''}`}
                    onClick={() => setSelectedId(p.id)}
                    data-testid="project-row"
                  >
                    <span className="project-row-dot" style={{ background: p.color }} />
                    <span className="project-row-info">
                      <span className="project-row-name">{p.name}</span>
                      <span className="project-row-meta">
                        {p.client_name ?? 'Personal'}
                      </span>
                    </span>
                    {p.hourly_rate && (
                      <span className="project-row-rate">${p.hourly_rate}/hr</span>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </aside>

      <section className="projects-main">
        {selected && (
          <>
            <header className="projects-main-head">
              <div className="projects-main-title-row">
                <span
                  className="projects-color-swatch"
                  style={{ background: selected.color }}
                />
                <div>
                  <p className="projects-eyebrow">
                    {selected.client_name ?? 'PERSONAL'}
                  </p>
                  <h1 className="projects-main-title">{selected.name}</h1>
                </div>
              </div>
              <button className="btn-primary">
                <Plus size={14} weight="bold" />
                New task
              </button>
            </header>

            <div className="projects-stats-row">
              <div className="project-stat">
                <FolderOpen size={14} color="var(--text-3)" />
                <span className="project-stat-label">Tasks</span>
                <span className="project-stat-value">{tasks.length}</span>
              </div>
              <div className="project-stat">
                <Clock size={14} color="var(--text-3)" />
                <span className="project-stat-label">Est</span>
                <span className="project-stat-value">
                  {totalEstimateHours.toFixed(1)}h
                </span>
              </div>
              <div className="project-stat">
                <Flag size={14} color="var(--text-3)" />
                <span className="project-stat-label">Urgent</span>
                <span className="project-stat-value">{urgentCount}</span>
              </div>
            </div>

            {tasksLoading ? (
              <p className="projects-loading">Loading tasks…</p>
            ) : (
              <ul className="tasks-list">
                {tasks.length === 0 ? (
                  <li className="tasks-empty">
                    No tasks yet. Click "New task" to add one.
                  </li>
                ) : (
                  tasks.map((task) => (
                    <li key={task.id} className="tasks-list-item">
                      <TaskCard task={task} />
                    </li>
                  ))
                )}
              </ul>
            )}
          </>
        )}

        {!selected && !projectsLoading && (
          <div className="projects-main-empty">
            Select a project from the sidebar.
          </div>
        )}
      </section>
    </main>
  )
}

export default ProjectsPage
