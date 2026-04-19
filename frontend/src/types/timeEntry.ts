export interface TimeEntry {
  id: string
  task_id: string
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
  created_at: string
}

export interface TimeEntryStart {
  task_id: string
  started_at?: string
}
