import type { Task, TaskPriority, TaskStatus } from '../types/task'

const PRIORITY_ORDER: Record<TaskPriority, number> = {
  urgent: 4,
  high: 3,
  medium: 2,
  low: 1,
}

export type SortKey = 'due_date_asc' | 'priority_desc' | 'title_asc'

export function filterByPriority(tasks: Task[], priority: TaskPriority | 'all'): Task[] {
  if (priority === 'all') return tasks
  return tasks.filter((t) => t.priority === priority)
}

export function filterByStatus(tasks: Task[], status: TaskStatus | 'all'): Task[] {
  if (status === 'all') return tasks
  return tasks.filter((t) => t.status === status)
}

export function filterByDueDateBefore(tasks: Task[], cutoff: string | null): Task[] {
  if (cutoff === null) return tasks
  return tasks.filter((t) => t.due_date !== null && t.due_date <= cutoff)
}

export function sortTasks(tasks: Task[], sortBy: SortKey): Task[] {
  const sorted = [...tasks]
  if (sortBy === 'due_date_asc') {
    sorted.sort((a, b) => {
      if (a.due_date === null && b.due_date === null) return 0
      if (a.due_date === null) return 1
      if (b.due_date === null) return -1
      return a.due_date.localeCompare(b.due_date)
    })
  } else if (sortBy === 'priority_desc') {
    sorted.sort((a, b) => PRIORITY_ORDER[b.priority] - PRIORITY_ORDER[a.priority])
  } else if (sortBy === 'title_asc') {
    sorted.sort((a, b) => a.title.localeCompare(b.title))
  }
  return sorted
}
