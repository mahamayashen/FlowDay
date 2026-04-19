import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { WeeklyReview } from '../types/weeklyReview'

export const WEEKLY_REVIEW_KEYS = {
  list: () => ['weekly-reviews'] as const,
  current: (weekStart: string) => ['weekly-reviews', 'current', weekStart] as const,
}

async function fetchWeeklyReview(weekStart: string): Promise<WeeklyReview | undefined> {
  const res = await apiClient.get(`/weekly-reviews/current?week_start=${weekStart}`)
  if (res.status === 404) return undefined
  if (!res.ok) throw new Error('Failed to fetch weekly review')
  return res.json() as Promise<WeeklyReview>
}

async function fetchWeeklyReviewHistory(limit: number): Promise<WeeklyReview[]> {
  const res = await apiClient.get(`/weekly-reviews?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch weekly review history')
  return res.json() as Promise<WeeklyReview[]>
}

async function generateWeeklyReview(weekStart: string): Promise<WeeklyReview> {
  const res = await apiClient.post('/weekly-reviews/generate', { week_start: weekStart })
  if (!res.ok) throw new Error('Failed to generate weekly review')
  return res.json() as Promise<WeeklyReview>
}

export function useWeeklyReview(weekStart: string) {
  return useQuery({
    queryKey: WEEKLY_REVIEW_KEYS.current(weekStart),
    queryFn: () => fetchWeeklyReview(weekStart),
    enabled: Boolean(weekStart),
    staleTime: 0,
    refetchInterval: (query) =>
      query.state.data?.status === 'generating' ? 4000 : false,
  })
}

export function useWeeklyReviewHistory(limit = 10) {
  return useQuery({
    queryKey: WEEKLY_REVIEW_KEYS.list(),
    queryFn: () => fetchWeeklyReviewHistory(limit),
  })
}

export function useGenerateWeeklyReview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (weekStart: string) => generateWeeklyReview(weekStart),
    onSuccess: (_result, weekStart) => {
      queryClient.invalidateQueries({ queryKey: WEEKLY_REVIEW_KEYS.list() })
      queryClient.invalidateQueries({ queryKey: WEEKLY_REVIEW_KEYS.current(weekStart) })
    },
  })
}
