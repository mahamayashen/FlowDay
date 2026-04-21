import { useState } from 'react'
import { Plus, FolderOpen, Clock, Flag } from '@phosphor-icons/react'
import { mockProjects, mockTasks } from '../mocks/data'
import type { Project } from '../types/project'
import type { Task, TaskPriority, TaskStatus } from '../types/task'
import './ProjectsPage.css'

const PRIORITY_COLORS: Record<TaskPriority, string> = {
  low: 'var(--text-3)',
  medium: 'var(--blue)',
  high: 'var(--yellow)',
  urgent: 'var(--danger)',
}

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'TO DO',
  in_progress: 'IN PROGRESS',
  done: 'DONE',
}

function ProjectsPage(): React.JSX.Element {
  const [selectedId, setSelectedId] = useState<string>(mockProjects[0]?.id ?? '')
  const selected: Project | undefined = mockProjects.find((p) => p.id === selectedId)
  const tasks: Task[] = mockTasks.filter((t) => t.project_id === selectedId)

  return (
    <main className="projects-page" data-testid="page-projects">
      <aside className="projects-sidebar">
        <div className="projects-sidebar-head">
          <h2 className="projects-sidebar-title">Projects</h2>
          <button className="btn-ghost" aria-label="Create project">
            <Plus size={16} weight="bold" />
          </button>
        </div>

        <ul className="projects-list">
          {mockProjects.map((p) => {
            const taskCount = mockTasks.filter((t) => t.project_id === p.id).length
            const active = p.id === selectedId
            return (
              <li key={p.id}>
                <button
                  className={`project-row${active ? ' project-row--active' : ''}`}
                  onClick={() => setSelectedId(p.id)}
                >
                  <span className="project-row-dot" style={{ background: p.color }} />
                  <span className="project-row-info">
                    <span className="project-row-name">{p.name}</span>
                    <span className="project-row-meta">
                      {p.client_name ?? 'Personal'} · {taskCount} {taskCount === 1 ? 'task' : 'tasks'}
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
      </aside>

      <section className="projects-main">
        {selected && (
          <>
            <header className="projects-main-head">
              <div className="projects-main-title-row">
                <span className="projects-color-swatch" style={{ background: selected.color }} />
                <div>
                  <p className="projects-eyebrow">{selected.client_name ?? 'PERSONAL'}</p>
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
                  {(tasks.reduce((s, t) => s + (t.estimate_minutes ?? 0), 0) / 60).toFixed(1)}h
                </span>
              </div>
              <div className="project-stat">
                <Flag size={14} color="var(--text-3)" />
                <span className="project-stat-label">Urgent</span>
                <span className="project-stat-value">
                  {tasks.filter((t) => t.priority === 'urgent' || t.priority === 'high').length}
                </span>
              </div>
            </div>

            <ul className="tasks-list">
              {tasks.length === 0 ? (
                <li className="tasks-empty">No tasks yet. Click "New task" to add one.</li>
              ) : (
                tasks.map((task) => (
                  <li key={task.id} className="task-card-v2">
                    <span
                      className="task-priority-bar"
                      style={{ background: PRIORITY_COLORS[task.priority] }}
                    />
                    <div className="task-card-v2-main">
                      <div className="task-card-v2-head">
                        <span
                          className={`task-status task-status--${task.status}`}
                        >
                          {STATUS_LABELS[task.status]}
                        </span>
                        {task.due_date && (
                          <span className="task-due">due {task.due_date.slice(5)}</span>
                        )}
                      </div>
                      <h3 className="task-card-v2-title">{task.title}</h3>
                      {task.description && (
                        <p className="task-card-v2-desc">{task.description}</p>
                      )}
                    </div>
                    <div className="task-card-v2-aside">
                      {task.estimate_minutes && (
                        <span className="task-estimate">
                          {(task.estimate_minutes / 60).toFixed(1)}h
                        </span>
                      )}
                    </div>
                  </li>
                ))
              )}
            </ul>
          </>
        )}
      </section>
    </main>
  )
}

export default ProjectsPage
