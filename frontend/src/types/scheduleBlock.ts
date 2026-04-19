export type ScheduleBlockSource = 'manual' | 'google_calendar'

export interface ScheduleBlock {
  id: string
  task_id: string
  date: string
  start_hour: number
  end_hour: number
  source: ScheduleBlockSource
  created_at: string
}

export interface ScheduleBlockCreate {
  task_id: string
  date: string
  start_hour: number
  end_hour: number
  source?: ScheduleBlockSource
}

export interface ScheduleBlockUpdate {
  date?: string
  start_hour?: number
  end_hour?: number
  source?: ScheduleBlockSource
}
