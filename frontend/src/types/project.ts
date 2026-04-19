export type ProjectStatus = 'active' | 'archived'

export interface Project {
  id: string
  user_id: string
  name: string
  color: string
  client_name: string | null
  hourly_rate: string | null
  status: ProjectStatus
  created_at: string
}

export interface ProjectCreate {
  name: string
  color: string
  client_name?: string | null
  hourly_rate?: string | null
}

export interface ProjectUpdate {
  name?: string
  color?: string
  client_name?: string | null
  hourly_rate?: string | null
  status?: ProjectStatus
}
