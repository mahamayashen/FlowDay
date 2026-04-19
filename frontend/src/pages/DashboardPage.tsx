import React, { useState } from 'react'
import './DashboardPage.css'
import { useProjects } from '../api/projects'
import { useProjectTasks } from '../api/tasks'
import ProjectCard from '../components/ProjectCard'
import ProjectForm from '../components/ProjectForm'
import TaskCard from '../components/TaskCard'
import TaskForm from '../components/TaskForm'
import TaskFilter from '../components/TaskFilter'
import { filterByPriority, filterByStatus, filterByDueDateBefore, sortTasks } from '../utils/taskFilters'
import type { TaskFilterState } from '../components/TaskFilter'
import type { Project } from '../types/project'
import type { Task } from '../types/task'

const DEFAULT_FILTER: TaskFilterState = {
  priority: 'all',
  status: 'all',
  sortBy: 'due_date_asc',
  dueDateBefore: null,
}

function DashboardPage(): React.JSX.Element {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [showProjectForm, setShowProjectForm] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [showTaskForm, setShowTaskForm] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [filter, setFilter] = useState<TaskFilterState>(DEFAULT_FILTER)

  const { data: projects, isLoading: projectsLoading, isError: projectsError } = useProjects()
  const { data: rawTasks, isLoading: tasksLoading, isError: tasksError } = useProjectTasks(selectedProjectId ?? '')

  const visibleTasks = selectedProjectId
    ? sortTasks(
        filterByStatus(
          filterByPriority(
            filterByDueDateBefore(rawTasks ?? [], filter.dueDateBefore),
            filter.priority,
          ),
          filter.status,
        ),
        filter.sortBy,
      )
    : []

  function openCreateProject(): void {
    setEditingProject(null)
    setShowProjectForm((v) => !v)
  }

  function openEditProject(project: Project): void {
    setShowProjectForm(false)
    setEditingProject((prev) => (prev?.id === project.id ? null : project))
  }

  function closeProjectForm(): void {
    setShowProjectForm(false)
    setEditingProject(null)
  }

  function openCreateTask(): void {
    setEditingTask(null)
    setShowTaskForm((v) => !v)
  }

  function openEditTask(task: Task): void {
    setShowTaskForm(false)
    setEditingTask((prev) => (prev?.id === task.id ? null : task))
  }

  function closeTaskForm(): void {
    setShowTaskForm(false)
    setEditingTask(null)
  }

  const projectFormVisible = showProjectForm || editingProject !== null
  const taskFormVisible = showTaskForm || editingTask !== null

  return (
    <main data-testid="page-dashboard" className="dashboard">
      <aside className="dashboard-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">Projects</h2>
          <button
            data-testid="btn-new-project"
            className="btn-icon"
            onClick={openCreateProject}
          >
            + New
          </button>
        </div>

        {projectFormVisible && (
          <div data-testid="project-form-panel" className="form-panel">
            <ProjectForm
              initialData={editingProject ?? undefined}
              onSuccess={closeProjectForm}
            />
          </div>
        )}

        {projectsLoading && (
          <span data-testid="projects-loading" className="loading-text">
            Loading…
          </span>
        )}

        {projectsError && (
          <span data-testid="projects-error" className="error-text">
            Failed to load projects.
          </span>
        )}

        <ul className="project-list">
          {(projects ?? []).map((project) => (
            <li key={project.id} className="project-list-item">
              <ProjectCard
                project={project}
                onClick={() => {
                  setSelectedProjectId(project.id)
                  closeTaskForm()
                  setFilter(DEFAULT_FILTER)
                }}
              />
              <button
                data-testid="btn-edit-project"
                className="btn-icon btn-edit"
                onClick={() => openEditProject(project)}
              >
                Edit
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className="dashboard-main">
        {selectedProjectId ? (
          <>
            {tasksError && (
              <span data-testid="tasks-error" className="error-text">
                Failed to load tasks.
              </span>
            )}

            {!tasksError && (
              <div className="task-toolbar">
                <TaskFilter value={filter} onChange={setFilter} />
                <button
                  data-testid="btn-new-task"
                  className="btn-icon"
                  onClick={openCreateTask}
                >
                  + New task
                </button>
              </div>
            )}

            {taskFormVisible && (
              <div data-testid="task-form-panel" className="form-panel">
                <TaskForm
                  projectId={selectedProjectId}
                  initialData={editingTask ?? undefined}
                  onSuccess={closeTaskForm}
                />
              </div>
            )}

            {tasksLoading && (
              <span data-testid="tasks-loading" className="loading-text">
                Loading…
              </span>
            )}

            <ul className="task-list">
              {visibleTasks.map((task) => (
                <li key={task.id} className="task-list-item">
                  <TaskCard task={task} />
                  <button
                    data-testid="btn-edit-task"
                    className="btn-icon btn-edit"
                    onClick={() => openEditTask(task)}
                  >
                    Edit
                  </button>
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
