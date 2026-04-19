import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { ScheduleBlock, ScheduleBlockCreate, ScheduleBlockUpdate } from '../types/scheduleBlock'

export const SCHEDULE_BLOCK_KEYS = {
  byDate: (date: string) => ['schedule-blocks', date] as const,
}

async function fetchScheduleBlocks(date: string): Promise<ScheduleBlock[]> {
  const res = await apiClient.get(`/schedule-blocks?date=${date}`)
  if (!res.ok) throw new Error('Failed to fetch schedule blocks')
  return res.json() as Promise<ScheduleBlock[]>
}

async function createScheduleBlock(data: ScheduleBlockCreate): Promise<ScheduleBlock> {
  const res = await apiClient.post('/schedule-blocks', data)
  if (!res.ok) throw new Error('Failed to create schedule block')
  return res.json() as Promise<ScheduleBlock>
}

async function updateScheduleBlock(blockId: string, data: ScheduleBlockUpdate): Promise<ScheduleBlock> {
  const res = await apiClient.put(`/schedule-blocks/${blockId}`, data)
  if (!res.ok) throw new Error('Failed to update schedule block')
  return res.json() as Promise<ScheduleBlock>
}

async function deleteScheduleBlock(blockId: string): Promise<void> {
  const res = await apiClient.delete(`/schedule-blocks/${blockId}`)
  if (!res.ok) throw new Error('Failed to delete schedule block')
}

export function useScheduleBlocks(date: string) {
  return useQuery({
    queryKey: SCHEDULE_BLOCK_KEYS.byDate(date),
    queryFn: () => fetchScheduleBlocks(date),
    enabled: Boolean(date),
  })
}

export function useCreateScheduleBlock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ data }: { data: ScheduleBlockCreate }) => createScheduleBlock(data),
    onSuccess: (_result, { data }) =>
      queryClient.invalidateQueries({ queryKey: SCHEDULE_BLOCK_KEYS.byDate(data.date) }),
  })
}

export function useUpdateScheduleBlock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ blockId, data }: { blockId: string; data: ScheduleBlockUpdate }) =>
      updateScheduleBlock(blockId, data),
    onSuccess: (_result, { data }) => {
      if (data.date) {
        queryClient.invalidateQueries({ queryKey: SCHEDULE_BLOCK_KEYS.byDate(data.date) })
      }
    },
  })
}

export function useDeleteScheduleBlock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ blockId, date }: { blockId: string; date: string }) => deleteScheduleBlock(blockId),
    onSuccess: (_result, { date }) =>
      queryClient.invalidateQueries({ queryKey: SCHEDULE_BLOCK_KEYS.byDate(date) }),
  })
}
