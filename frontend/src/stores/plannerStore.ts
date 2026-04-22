import { create } from 'zustand'
import { formatLocalDate } from '../utils/reviewUtils'

// A ScheduleBlock's `date` is a user-facing calendar day, not a timestamp.
// Always derive it from the user's *local* clock so "today" means the day
// the user sees on the wall. Using `toISOString().slice(0, 10)` would
// return UTC, which is ahead of local in negative-offset timezones after
// ~5pm local — leading to blocks saved under the wrong date and Today
// queries returning empty.

function todayString(): string {
  return formatLocalDate(new Date())
}

function shiftDate(dateStr: string, days: number): string {
  // Parse the stored string as local midnight and shift in local time.
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return formatLocalDate(d)
}

interface PlannerState {
  selectedDate: string
  workHoursStart: number
  workHoursEnd: number
  setSelectedDate: (date: string) => void
  goToNextDay: () => void
  goToPrevDay: () => void
  setWorkHours: (start: number, end: number) => void
}

export const usePlannerStore = create<PlannerState>((set, get) => ({
  selectedDate: todayString(),
  workHoursStart: 8,
  workHoursEnd: 18,
  setSelectedDate: (date) => set({ selectedDate: date }),
  goToNextDay: () => set({ selectedDate: shiftDate(get().selectedDate, 1) }),
  goToPrevDay: () => set({ selectedDate: shiftDate(get().selectedDate, -1) }),
  setWorkHours: (start, end) => set({ workHoursStart: start, workHoursEnd: end }),
}))
