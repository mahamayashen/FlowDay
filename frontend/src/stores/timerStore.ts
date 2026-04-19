import { create } from 'zustand'

interface TimerState {
  activeEntryId: string | null
  activeTaskId: string | null
  startTick: (entryId: string, startedAt: string) => void
  stopTick: () => void
  isTaskTimerActive: (taskId: string) => boolean
}

let _tickInterval: ReturnType<typeof setInterval> | null = null

export const useTimerStore = create<TimerState>((set, get) => ({
  activeEntryId: null,
  activeTaskId: null,

  startTick: (entryId, _startedAt) => {
    // Clear any existing interval before starting a new one
    if (_tickInterval !== null) {
      clearInterval(_tickInterval)
      _tickInterval = null
    }
    set({ activeEntryId: entryId })
  },

  stopTick: () => {
    if (_tickInterval !== null) {
      clearInterval(_tickInterval)
      _tickInterval = null
    }
    set({ activeEntryId: null, activeTaskId: null })
  },

  isTaskTimerActive: (taskId) => {
    return get().activeTaskId === taskId
  },
}))
