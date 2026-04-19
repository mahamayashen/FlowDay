import React from 'react'
import { useDraggable } from '@dnd-kit/core'
import type { Project } from '../types/project'
import type { Task } from '../types/task'
import './TaskPool.css'

interface DraggableTaskProps {
  task: Task
  projectColor: string
}

function DraggableTask({ task, projectColor }: DraggableTaskProps): React.JSX.Element {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id,
    data: { type: 'task', task },
  })

  return (
    <div
      ref={setNodeRef}
      className={`task-pool-item${isDragging ? ' dragging' : ''}`}
      data-testid={`pool-task-${task.id}`}
      style={{ borderLeftColor: projectColor }}
      {...listeners}
      {...attributes}
    >
      {task.title}
    </div>
  )
}

interface TaskPoolProps {
  projects: Project[]
  tasksByProject: Map<string, Task[]>
}

function TaskPool({ projects, tasksByProject }: TaskPoolProps): React.JSX.Element {
  return (
    <div className="task-pool" data-testid="task-pool">
      <div className="task-pool-header">Unscheduled</div>
      {projects.map((project) => {
        const tasks = tasksByProject.get(project.id) ?? []
        if (tasks.length === 0) return null
        return (
          <div key={project.id} className="task-pool-group">
            <div className="task-pool-group-header">
              <span
                className="task-pool-color-swatch"
                style={{ backgroundColor: project.color }}
              />
              {project.name}
            </div>
            {tasks.map((task) => (
              <DraggableTask key={task.id} task={task} projectColor={project.color} />
            ))}
          </div>
        )
      })}
    </div>
  )
}

export default TaskPool
