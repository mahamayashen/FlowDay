import React, { useState } from 'react'
import './ProjectForm.css'
import { useCreateProject, useUpdateProject } from '../api/projects'
import { isValidHex } from '../utils/validation'
import type { Project } from '../types/project'

interface ProjectFormProps {
  initialData?: Project
  onSuccess: () => void
}

function ProjectForm({ initialData, onSuccess }: ProjectFormProps): React.JSX.Element {
  const isEdit = Boolean(initialData)

  const [name, setName] = useState(initialData?.name ?? '')
  const [color, setColor] = useState(initialData?.color ?? '#f59e0b')
  const [clientName, setClientName] = useState(initialData?.client_name ?? '')
  const [hourlyRate, setHourlyRate] = useState(initialData?.hourly_rate ?? '')
  const [errors, setErrors] = useState<{ name?: string; color?: string }>({})

  const createProject = useCreateProject()
  const updateProject = useUpdateProject()

  function validate(): boolean {
    const next: { name?: string; color?: string } = {}
    if (!name.trim()) next.name = 'Name is required'
    if (!isValidHex(color)) next.color = 'Color must be a valid hex code (e.g. #f59e0b)'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  function handleSubmit(e: React.FormEvent): void {
    e.preventDefault()
    if (!validate()) return

    const payload = {
      name: name.trim(),
      color,
      client_name: clientName.trim() || null,
      hourly_rate: hourlyRate.trim() || null,
    }

    if (isEdit && initialData) {
      updateProject.mutate({ id: initialData.id, data: payload }, { onSuccess })
    } else {
      createProject.mutate(payload, { onSuccess })
    }
  }

  return (
    <form
      aria-label="project form"
      role="form"
      className="project-form"
      onSubmit={handleSubmit}
    >
      <div className="form-field">
        <label htmlFor="project-name">Name</label>
        <input
          id="project-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {errors.name && (
          <span data-testid="form-error-name" className="form-field-error">
            {errors.name}
          </span>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="project-color">Color</label>
        <input
          id="project-color"
          type="text"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          placeholder="#f59e0b"
        />
        {errors.color && (
          <span data-testid="form-error-color" className="form-field-error">
            {errors.color}
          </span>
        )}
      </div>

      <div className="form-field">
        <label htmlFor="project-client">Client name</label>
        <input
          id="project-client"
          type="text"
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
          placeholder="Optional"
        />
      </div>

      <div className="form-field">
        <label htmlFor="project-hourly-rate">Hourly rate</label>
        <input
          id="project-hourly-rate"
          type="number"
          min="0"
          step="0.01"
          value={hourlyRate}
          onChange={(e) => setHourlyRate(e.target.value)}
          placeholder="Optional"
        />
      </div>

      <button
        type="submit"
        className="project-form-submit"
        disabled={createProject.isPending || updateProject.isPending}
      >
        {isEdit ? 'Save changes' : 'Create project'}
      </button>
    </form>
  )
}

export default ProjectForm
