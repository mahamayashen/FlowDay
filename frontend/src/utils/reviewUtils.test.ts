import { describe, it, expect } from 'vitest'
import {
  statusTagColor,
  formatAccuracy,
  toWeeklyChartData,
  getWeekStart,
} from './reviewUtils'
import type { ProjectWeeklyStats } from '../types/analytics'

function makeProjectStats(overrides: Partial<ProjectWeeklyStats>): ProjectWeeklyStats {
  return {
    project_id: 'proj-1',
    project_name: 'FlowDay',
    project_color: '#f59e0b',
    planned_hours: 8,
    actual_hours: 6,
    accuracy_pct: 75,
    ...overrides,
  }
}

describe('statusTagColor', () => {
  it('returns green for done', () => {
    expect(statusTagColor('done')).toBe('#22c55e')
  })

  it('returns yellow for partial', () => {
    expect(statusTagColor('partial')).toBe('#eab308')
  })

  it('returns red for skipped', () => {
    expect(statusTagColor('skipped')).toBe('#ef4444')
  })

  it('returns blue for unplanned', () => {
    expect(statusTagColor('unplanned')).toBe('#3b82f6')
  })
})

describe('formatAccuracy', () => {
  it('rounds to one decimal place', () => {
    expect(formatAccuracy(87.567)).toBe('87.6%')
  })

  it('returns 0.0% for zero', () => {
    expect(formatAccuracy(0)).toBe('0.0%')
  })

  it('returns 100.0% for perfect accuracy', () => {
    expect(formatAccuracy(100)).toBe('100.0%')
  })
})

describe('toWeeklyChartData', () => {
  it('maps projects to chart entries with name, planned, actual, color', () => {
    const stats = [
      makeProjectStats({ project_name: 'Alpha', planned_hours: 4, actual_hours: 3, project_color: '#ff0000' }),
      makeProjectStats({ project_id: 'proj-2', project_name: 'Beta', planned_hours: 2, actual_hours: 2, project_color: '#00ff00' }),
    ]
    const result = toWeeklyChartData(stats)
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ name: 'Alpha', planned: 4, actual: 3, color: '#ff0000' })
    expect(result[1]).toEqual({ name: 'Beta', planned: 2, actual: 2, color: '#00ff00' })
  })

  it('returns empty array for empty input', () => {
    expect(toWeeklyChartData([])).toEqual([])
  })

  it('rounds hours to two decimal places', () => {
    const stats = [makeProjectStats({ planned_hours: 1.3333, actual_hours: 0.6667 })]
    const result = toWeeklyChartData(stats)
    expect(result[0].planned).toBe(1.33)
    expect(result[0].actual).toBe(0.67)
  })
})

describe('getWeekStart', () => {
  it('returns Monday for a Wednesday input', () => {
    expect(getWeekStart('2026-04-22')).toBe('2026-04-20')
  })

  it('returns the same day for a Monday input', () => {
    expect(getWeekStart('2026-04-20')).toBe('2026-04-20')
  })

  it('returns the previous Monday for a Sunday input', () => {
    expect(getWeekStart('2026-04-19')).toBe('2026-04-13')
  })
})
