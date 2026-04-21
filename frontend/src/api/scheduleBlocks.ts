import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { ScheduleBlock, ScheduleBlockCreate, ScheduleBlockUpdate } from '../types/scheduleBlock'

export const SCHEDULE_BLOCK_KEYS = {
  byDate: (date: string) => ['schedule-blocks', date] as const,
}

// Backend stores start_hour / end_hour as Decimal. Pydantic v2 serializes
// Decimal as a JSON string (e.g. "9.5") to preserve precision, but the
// frontend treats these as numbers for arithmetic (drag/resize math in
// ScheduleBlockItem would otherwise do string concat — "9.0" + 0.25 = "9.00.25").
// Coerce at the edge so downstream code can trust the types.
interface RawScheduleBlock extends Omit<ScheduleBlock, 'start_hour' | 'end_hour'> {
  start_hour: number | string
  end_hour: number | string
}

function normalizeBlock(raw: RawScheduleBlock): ScheduleBlock {
  return {
    ...raw,
    start_hour: typeof raw.start_hour === 'string' ? parseFloat(raw.start_hour) : raw.start_hour,
    end_hour: typeof raw.end_hour === 'string' ? parseFloat(raw.end_hour) : raw.end_hour,
  }
}

async function fetchScheduleBlocks(date: string): Promise<ScheduleBlock[]> {
  const res = await apiClient.get(`/schedule-blocks?date=${date}`)
  if (!res.ok) throw new Error('Failed to fetch schedule blocks')
  const list = (await res.json()) as RawScheduleBlock[]
  return list.map(normalizeBlock)
}

async function createScheduleBlock(data: ScheduleBlockCreate): Promise<ScheduleBlock> {
  const res = await apiClient.post('/schedule-blocks', data)
  if (!res.ok) throw new Error('Failed to create schedule block')
  const raw = (await res.json()) as RawScheduleBlock
  return normalizeBlock(raw)
}

async function updateScheduleBlock(blockId: string, data: ScheduleBlockUpdate): Promise<ScheduleBlock> {
  const res = await apiClient.put(`/schedule-blocks/${blockId}`, data)
  if (!res.ok) throw new Error('Failed to update schedule block')
  const raw = (await res.json()) as RawScheduleBlock
  return normalizeBlock(raw)
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
    mutationFn: ({ blockId, data }: { blockId: string; data: ScheduleBlockUpdate; originalDate: string }) =>
      updateScheduleBlock(blockId, data),
    onSuccess: (_result, { data, originalDate }) => {
      queryClient.invalidateQueries({ queryKey: SCHEDULE_BLOCK_KEYS.byDate(originalDate) })
      if (data.date && data.date !== originalDate) {
        queryClient.invalidateQueries({ queryKey: SCHEDULE_BLOCK_KEYS.byDate(data.date) })
      }
    },
  })
}

export function useDeleteScheduleBlock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ blockId }: { blockId: string; date: string }) => deleteScheduleBlock(blockId),
    onSuccess: (_result, { date }) =>
      queryClient.invalidateQueries({ queryKey: SCHEDULE_BLOCK_KEYS.byDate(date) }),
  })
}
