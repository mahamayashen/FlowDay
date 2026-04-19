import React from 'react'
import './TaskFilter.css'
import type { TaskPriority, TaskStatus } from '../types/task'
import type { SortKey } from '../utils/taskFilters'

export interface TaskFilterState {
  priority: TaskPriority | 'all'
  status: TaskStatus | 'all'
  sortBy: SortKey
  dueDateBefore: string | null
}

interface TaskFilterProps {
  value: TaskFilterState
  onChange: (next: TaskFilterState) => void
}

function TaskFilter({ value, onChange }: TaskFilterProps): React.JSX.Element {
  return (
    <div className="task-filter" data-testid="task-filter">
      <div className="form-field">
        <label htmlFor="filter-priority">Priority</label>
        <select
          id="filter-priority"
          value={value.priority}
          onChange={(e) => onChange({ ...value, priority: e.target.value as TaskPriority | 'all' })}
        >
          <option value="all">All</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="filter-status">Status</label>
        <select
          id="filter-status"
          value={value.status}
          onChange={(e) => onChange({ ...value, status: e.target.value as TaskStatus | 'all' })}
        >
          <option value="all">All</option>
          <option value="todo">Todo</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="filter-sort">Sort by</label>
        <select
          id="filter-sort"
          value={value.sortBy}
          onChange={(e) => onChange({ ...value, sortBy: e.target.value as SortKey })}
        >
          <option value="due_date_asc">Due date</option>
          <option value="priority_desc">Priority</option>
          <option value="title_asc">Title</option>
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="filter-due-before">Due before</label>
        <input
          id="filter-due-before"
          type="date"
          value={value.dueDateBefore ?? ''}
          onChange={(e) =>
            onChange({ ...value, dueDateBefore: e.target.value || null })
          }
        />
      </div>
    </div>
  )
}

export default TaskFilter
