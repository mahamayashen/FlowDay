import React, { useState } from 'react'
import './DashboardPage.css'
import { useProjects } from '../api/projects'
import { useProjectTasks } from '../api/tasks'
import ProjectCard from '../components/ProjectCard'
import ProjectForm from '../components/ProjectForm'
import TaskCard from '../components/TaskCard'
import TaskForm from '../components/TaskForm'
import TaskFilter from '../components/TaskFilter'
import { filterByPriority, filterByStatus, sortTasks } from '../utils/taskFilters'
import type { TaskFilterState } from '../components/TaskFilter'

const DEFAULT_FILTER: TaskFilterState = {
  priority: 'all',
  status: 'all',
  sortBy: 'due_date_asc',
}

function DashboardPage(): React.JSX.Element {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [showProjectForm, setShowProjectForm] = useState(false)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [filter, setFilter] = useState<TaskFilterState>(DEFAULT_FILTER)

  const { data: projects, isLoading: projectsLoading } = useProjects()
  const { data: rawTasks } = useProjectTasks(selectedProjectId ?? '')

  const visibleTasks = selectedProjectId
    ? sortTasks(
        filterByStatus(
          filterByPriority(rawTasks ?? [], filter.priority),
          filter.status,
        ),
        filter.sortBy,
      )
    : []

  return (
    <main data-testid="page-dashboard" className="dashboard">
      <aside className="dashboard-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">Projects</h2>
          <button
            data-testid="btn-new-project"
            className="btn-icon"
            onClick={() => setShowProjectForm((v) => !v)}
          >
            + New
          </button>
        </div>

        {showProjectForm && (
          <div data-testid="project-form-panel" className="form-panel">
            <ProjectForm onSuccess={() => setShowProjectForm(false)} />
          </div>
        )}

        {projectsLoading && (
          <span data-testid="projects-loading" className="loading-text">
            Loading…
          </span>
        )}

        <ul className="project-list">
          {(projects ?? []).map((project) => (
            <li key={project.id}>
              <ProjectCard
                project={project}
                onClick={() => {
                  setSelectedProjectId(project.id)
                  setShowTaskForm(false)
                  setFilter(DEFAULT_FILTER)
                }}
              />
            </li>
          ))}
        </ul>
      </aside>

      <section className="dashboard-main">
        {selectedProjectId ? (
          <>
            <div className="task-toolbar">
              <TaskFilter value={filter} onChange={setFilter} />
              <button
                data-testid="btn-new-task"
                className="btn-icon"
                onClick={() => setShowTaskForm((v) => !v)}
              >
                + New task
              </button>
            </div>

            {showTaskForm && (
              <div data-testid="task-form-panel" className="form-panel">
                <TaskForm
                  projectId={selectedProjectId}
                  onSuccess={() => setShowTaskForm(false)}
                />
              </div>
            )}

            <ul className="task-list">
              {visibleTasks.map((task) => (
                <li key={task.id}>
                  <TaskCard task={task} />
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="empty-state">Select a project to view tasks.</p>
        )}
      </section>
    </main>
  )
}

export default DashboardPage
