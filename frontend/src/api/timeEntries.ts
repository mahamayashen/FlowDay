import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { TimeEntry, TimeEntryStart } from '../types/timeEntry'

export const TIME_ENTRY_KEYS = {
  all: ['time-entries'] as const,
  active: ['time-entries', 'active'] as const,
}

async function fetchTimeEntries(): Promise<TimeEntry[]> {
  const res = await apiClient.get('/time-entries')
  if (!res.ok) throw new Error('Failed to fetch time entries')
  return res.json() as Promise<TimeEntry[]>
}

async function startTimer(data: TimeEntryStart): Promise<TimeEntry> {
  const res = await apiClient.post('/time-entries/start', data)
  if (!res.ok) throw new Error('Failed to start timer')
  return res.json() as Promise<TimeEntry>
}

async function stopTimer(entryId: string): Promise<TimeEntry> {
  const res = await apiClient.post(`/time-entries/${entryId}/stop`)
  if (!res.ok) throw new Error('Failed to stop timer')
  return res.json() as Promise<TimeEntry>
}

export function useActiveTimer() {
  return useQuery({
    queryKey: TIME_ENTRY_KEYS.active,
    queryFn: async () => {
      const entries = await fetchTimeEntries()
      return entries.find((e) => e.ended_at === null) ?? null
    },
  })
}

export function useStartTimer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: TimeEntryStart) => startTimer(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TIME_ENTRY_KEYS.active }),
  })
}

export function useStopTimer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (entryId: string) => stopTimer(entryId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TIME_ENTRY_KEYS.active }),
  })
}
