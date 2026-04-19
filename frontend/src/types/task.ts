export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent'
export type TaskStatus = 'todo' | 'in_progress' | 'done'

export interface Task {
  id: string
  project_id: string
  title: string
  description: string | null
  estimate_minutes: number | null
  priority: TaskPriority
  status: TaskStatus
  due_date: string | null
  created_at: string
  completed_at: string | null
}

export interface TaskCreate {
  title: string
  description?: string | null
  estimate_minutes?: number | null
  priority?: TaskPriority
  status?: TaskStatus
  due_date?: string | null
}

export interface TaskUpdate {
  title?: string
  description?: string | null
  estimate_minutes?: number | null
  priority?: TaskPriority
  status?: TaskStatus
  due_date?: string | null
}
