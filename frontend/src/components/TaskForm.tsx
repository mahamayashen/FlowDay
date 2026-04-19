import React, { useState } from 'react'
import './TaskForm.css'
import { useCreateTask, useUpdateTask } from '../api/tasks'
import type { Task, TaskPriority, TaskStatus } from '../types/task'

interface TaskFormProps {
  projectId: string
  initialData?: Task
  onSuccess: () => void
}

function TaskForm({ projectId, initialData, onSuccess }: TaskFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData)

  const [title, setTitle] = useState(initialData?.title ?? '')
  const [estimate, setEstimate] = useState(
    initialData?.estimate_minutes != null ? String(initialData.estimate_minutes) : '',
  )
  const [priority, setPriority] = useState<TaskPriority>(initialData?.priority ?? 'medium')
  const [status, setStatus] = useState<TaskStatus>(initialData?.status ?? 'todo')
  const [dueDate, setDueDate] = useState(initialData?.due_date ?? '')
  const [errors, setErrors] = useState<{ title?: string; estimate?: string }>({})

  const createTask = useCreateTask()
  const updateTask = useUpdateTask()

  function validate(): boolean {
    const next: { title?: string; estimate?: string } = {}
    if (!title.trim()) next.title = 'Title is required'
    if (estimate !== '' && Number(estimate) < 0) next.estimate = 'Estimate must be 0 or greater'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  function handleSubmit(e: React.FormEvent): void {
    e.preventDefault()
    if (!validate()) return

    const data = {
      title: title.trim(),
      priority,
      status,
      estimate_minutes: estimate !== '' ? Number(estimate) : null,
      due_date: dueDate || null,
    }

    if (isEdit && initialData) {
      updateTask.mutate({ projectId, taskId: initialData.id, data }, { onSuccess })
    } else {
      createTask.mutate({ projectId, data }, { onSuccess })
    }
  }

  return (
    <form role="form" className="task-form" onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="task-title">Title</label>
        <input
          id="task-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        {errors.title && (
          <span data-testid="form-error-title" className="form-field-error">
            {errors.title}
          </span>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="task-estimate">Estimate (minutes)</label>
        <input
          id="task-estimate"
          type="number"
          min="0"
          value={estimate}
          onChange={(e) => setEstimate(e.target.value)}
          placeholder="Optional"
        />
        {errors.estimate && (
          <span data-testid="form-error-estimate" className="form-field-error">
            {errors.estimate}
          </span>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="task-priority">Priority</label>
        <select
          id="task-priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as TaskPriority)}
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="task-status">Status</label>
        <select
          id="task-status"
          value={status}
          onChange={(e) => setStatus(e.target.value as TaskStatus)}
        >
          <option value="todo">Todo</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="task-due-date">Due date</label>
        <input
          id="task-due-date"
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
        />
      </div>

      <button
        type="submit"
        className="task-form-submit"
        disabled={createTask.isPending || updateTask.isPending}
      >
        {isEdit ? 'Save changes' : 'Create task'}
      </button>
    </form>
  )
}

export default TaskForm
