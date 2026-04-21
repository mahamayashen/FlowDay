import React, { useState, useEffect } from 'react'
import { Plus, FolderOpen, Clock, Flag, PencilSimple, Trash } from '@phosphor-icons/react'
import { useProjects, useDeleteProject } from '../api/projects'
import { useProjectTasks } from '../api/tasks'
import TaskCard from '../components/TaskCard'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import ProjectForm from '../components/ProjectForm'
import TaskForm from '../components/TaskForm'
import type { Project } from '../types/project'
import type { Task } from '../types/task'
import './ProjectsPage.css'

type ProjectModalState =
  | { kind: 'closed' }
  | { kind: 'create' }
  | { kind: 'edit'; project: Project }

type TaskModalState =
  | { kind: 'closed' }
  | { kind: 'create' }
  | { kind: 'edit'; task: Task }

function ProjectsPage(): React.JSX.Element {
  const { data: projects = [], isLoading: projectsLoading } = useProjects()
  const [selectedId, setSelectedId] = useState<string>('')

  // Select the first project once the list lands.
  useEffect(() => {
    if (!selectedId && projects.length > 0) {
      setSelectedId(projects[0].id)
    }
  }, [projects, selectedId])

  // If the currently-selected project was deleted, fall back to the first remaining one.
  useEffect(() => {
    if (selectedId && projects.length > 0 && !projects.some((p) => p.id === selectedId)) {
      setSelectedId(projects[0].id)
    } else if (projects.length === 0 && selectedId) {
      setSelectedId('')
    }
  }, [projects, selectedId])

  const { data: tasks = [], isLoading: tasksLoading } = useProjectTasks(selectedId)
  const selected: Project | undefined = projects.find((p) => p.id === selectedId)

  const totalEstimateHours =
    tasks.reduce((s, t) => s + (t.estimate_minutes ?? 0), 0) / 60
  const urgentCount = tasks.filter(
    (t) => t.priority === 'urgent' || t.priority === 'high',
  ).length

  // ── Modal state ──
  const [projectModal, setProjectModal] = useState<ProjectModalState>({ kind: 'closed' })
  const [taskModal, setTaskModal] = useState<TaskModalState>({ kind: 'closed' })
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null)

  const deleteProject = useDeleteProject()

  function handleConfirmDeleteProject(): void {
    if (!projectToDelete) return
    deleteProject.mutate(projectToDelete.id, {
      onSuccess: () => setProjectToDelete(null),
    })
  }

  return (
    <main className="projects-page" data-testid="page-projects">
      <aside className="projects-sidebar">
        <div className="projects-sidebar-head">
          <h2 className="projects-sidebar-title">Projects</h2>
          <button
            className="btn-ghost"
            aria-label="Create project"
            onClick={() => setProjectModal({ kind: 'create' })}
            data-testid="btn-create-project"
          >
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
                <li key={p.id} className="project-row-wrap">
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
                  <div className="project-row-actions">
                    <button
                      type="button"
                      className="row-action-btn"
                      aria-label={`Edit project ${p.name}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        setProjectModal({ kind: 'edit', project: p })
                      }}
                      data-testid="btn-edit-project"
                    >
                      <PencilSimple size={12} weight="bold" />
                    </button>
                    <button
                      type="button"
                      className="row-action-btn row-action-btn--danger"
                      aria-label={`Delete project ${p.name}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        setProjectToDelete(p)
                      }}
                      data-testid="btn-delete-project"
                    >
                      <Trash size={12} weight="bold" />
                    </button>
                  </div>
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
              <button
                className="btn-primary"
                onClick={() => setTaskModal({ kind: 'create' })}
                data-testid="btn-create-task"
              >
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
                      <TaskCard
                        task={task}
                        projectId={selected.id}
                        onEdit={() => setTaskModal({ kind: 'edit', task })}
                      />
                    </li>
                  ))
                )}
              </ul>
            )}
          </>
        )}

        {!selected && !projectsLoading && (
          <div className="projects-main-empty">
            {projects.length === 0
              ? 'Create your first project from the sidebar.'
              : 'Select a project from the sidebar.'}
          </div>
        )}
      </section>

      {/* ── Project create/edit modal ── */}
      <Modal
        open={projectModal.kind !== 'closed'}
        onClose={() => setProjectModal({ kind: 'closed' })}
        title={projectModal.kind === 'edit' ? 'Edit project' : 'New project'}
      >
        {projectModal.kind !== 'closed' && (
          <ProjectForm
            initialData={projectModal.kind === 'edit' ? projectModal.project : undefined}
            onSuccess={() => setProjectModal({ kind: 'closed' })}
          />
        )}
      </Modal>

      {/* ── Task create/edit modal ── */}
      <Modal
        open={taskModal.kind !== 'closed'}
        onClose={() => setTaskModal({ kind: 'closed' })}
        title={taskModal.kind === 'edit' ? 'Edit task' : 'New task'}
      >
        {taskModal.kind !== 'closed' && selected && (
          <TaskForm
            projectId={selected.id}
            initialData={taskModal.kind === 'edit' ? taskModal.task : undefined}
            onSuccess={() => setTaskModal({ kind: 'closed' })}
          />
        )}
      </Modal>

      {/* ── Project delete confirmation ── */}
      <ConfirmDialog
        open={projectToDelete !== null}
        title="Delete project?"
        message={
          <>
            This will permanently delete <strong>{projectToDelete?.name}</strong> and
            all of its tasks. This action cannot be undone.
          </>
        }
        confirmLabel="Delete project"
        onConfirm={handleConfirmDeleteProject}
        onCancel={() => setProjectToDelete(null)}
        isPending={deleteProject.isPending}
      />
    </main>
  )
}

export default ProjectsPage
