import { create } from 'zustand'

interface TimerState {
  activeEntryId: string | null
  activeTaskId: string | null
  startTick: (entryId: string, taskId?: string) => void
  stopTick: () => void
  isTaskTimerActive: (taskId: string) => boolean
}

export const useTimerStore = create<TimerState>((set, get) => ({
  activeEntryId: null,
  activeTaskId: null,

  startTick: (entryId, taskId) => {
    set({ activeEntryId: entryId, activeTaskId: taskId ?? null })
  },

  stopTick: () => {
    set({ activeEntryId: null, activeTaskId: null })
  },

  isTaskTimerActive: (taskId) => {
    return get().activeTaskId === taskId
  },
}))
