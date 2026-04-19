import { create } from 'zustand'

function todayString(): string {
  return new Date().toISOString().slice(0, 10)
}

function shiftDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T12:00:00Z')
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
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
