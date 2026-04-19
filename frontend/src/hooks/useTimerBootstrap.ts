import { useEffect } from 'react'
import { useActiveTimer } from '../api/timeEntries'
import { useTimerStore } from '../stores/timerStore'

export function useTimerBootstrap(): void {
  const { data: activeEntry } = useActiveTimer()
  const startTick = useTimerStore((s) => s.startTick)
  const stopTick = useTimerStore((s) => s.stopTick)

  useEffect(() => {
    if (activeEntry) {
      startTick(activeEntry.id, activeEntry.task_id)
    } else if (activeEntry === null) {
      stopTick()
    }
  }, [activeEntry, startTick, stopTick])
}
