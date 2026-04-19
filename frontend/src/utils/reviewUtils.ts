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

export function getWeekStart(date: string): string {
  const d = new Date(date + 'T00:00:00')
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return d.toISOString().slice(0, 10)
}
