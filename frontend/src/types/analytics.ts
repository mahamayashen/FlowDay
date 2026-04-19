export type StatusTag = 'done' | 'partial' | 'skipped' | 'unplanned'

export interface TaskComparison {
  task_id: string
  task_title: string
  planned_hours: number
  actual_hours: number
  status: StatusTag
}

export interface PlannedVsActualSummary {
  total_planned_hours: number
  total_actual_hours: number
  done_count: number
  partial_count: number
  skipped_count: number
  unplanned_count: number
}

export interface PlannedVsActualResponse {
  date: string
  tasks: TaskComparison[]
  summary: PlannedVsActualSummary
}

export interface ProjectWeeklyStats {
  project_id: string
  project_name: string
  project_color: string
  planned_hours: number
  actual_hours: number
  accuracy_pct: number
}

export interface WeeklyStatsSummary {
  total_planned_hours: number
  total_actual_hours: number
  average_accuracy_pct: number
}

export interface WeeklyStatsResponse {
  week_start: string
  week_end: string
  projects: ProjectWeeklyStats[]
  summary: WeeklyStatsSummary
}

export interface WeeklyChartEntry {
  name: string
  planned: number
  actual: number
  color: string
}
