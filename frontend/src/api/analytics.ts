import { useQuery } from '@tanstack/react-query'
import { apiClient } from './client'
import type { PlannedVsActualResponse, WeeklyStatsResponse } from '../types/analytics'

export const ANALYTICS_KEYS = {
  plannedVsActual: (date: string) => ['analytics', 'planned-vs-actual', date] as const,
  weeklyStats: (weekStart: string) => ['analytics', 'weekly-stats', weekStart] as const,
}

async function fetchPlannedVsActual(date: string): Promise<PlannedVsActualResponse> {
  const res = await apiClient.get(`/analytics/planned-vs-actual?date=${date}`)
  if (!res.ok) throw new Error('Failed to fetch planned vs actual')
  return res.json() as Promise<PlannedVsActualResponse>
}

async function fetchWeeklyStats(weekStart: string): Promise<WeeklyStatsResponse> {
  const res = await apiClient.get(`/analytics/weekly-stats?week_start=${weekStart}`)
  if (!res.ok) throw new Error('Failed to fetch weekly stats')
  return res.json() as Promise<WeeklyStatsResponse>
}

export function usePlannedVsActual(date: string) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.plannedVsActual(date),
    queryFn: () => fetchPlannedVsActual(date),
    enabled: Boolean(date),
  })
}

export function useWeeklyStats(weekStart: string) {
  return useQuery({
    queryKey: ANALYTICS_KEYS.weeklyStats(weekStart),
    queryFn: () => fetchWeeklyStats(weekStart),
    enabled: Boolean(weekStart),
  })
}
