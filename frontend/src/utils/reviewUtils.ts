import type { StatusTag, ProjectWeeklyStats, WeeklyChartEntry } from '../types/analytics'

export function statusTagColor(status: StatusTag): string {
  switch (status) {
    case 'done':
      return '#22c55e'
    case 'partial':
      return '#eab308'
    case 'skipped':
      return '#ef4444'
    case 'unplanned':
      return '#3b82f6'
  }
}

export function formatAccuracy(pct: number): string {
  return pct.toFixed(1) + '%'
}

export function toWeeklyChartData(projects: ProjectWeeklyStats[]): WeeklyChartEntry[] {
  return projects.map((p) => ({
    name: p.project_name,
    planned: Math.round(p.planned_hours * 100) / 100,
    actual: Math.round(p.actual_hours * 100) / 100,
    color: p.project_color,
  }))
}

export function formatLocalDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function addWeeks(weekStart: string, weeks: number): string {
  const d = new Date(weekStart + 'T00:00:00')
  d.setDate(d.getDate() + weeks * 7)
  return formatLocalDate(d)
}

export function getWeekStart(date: string): string {
  const d = new Date(date + 'T00:00:00')
  const dow = d.getDay()
  const diff = dow === 0 ? -6 : 1 - dow
  d.setDate(d.getDate() + diff)
  return formatLocalDate(d)
}
