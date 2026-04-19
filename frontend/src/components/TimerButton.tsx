import React, { useEffect, useState } from 'react'
import './TimerButton.css'
import type { TimeEntry } from '../types/timeEntry'

interface TimerButtonProps {
  activeEntry: TimeEntry | null
  onStart: () => void
  onStop: (entryId: string) => void
}

function formatElapsed(seconds: number): string {
  const mm = Math.floor(seconds / 60).toString().padStart(2, '0')
  const ss = (seconds % 60).toString().padStart(2, '0')
  return `${mm}:${ss}`
}

function TimerButton({ activeEntry, onStart, onStop }: TimerButtonProps): React.JSX.Element {
  const [elapsed, setElapsed] = useState<number>(0)

  useEffect(() => {
    if (!activeEntry) {
      setElapsed(0)
      return
    }
    // Compute initial elapsed from wall clock
    const initial = Math.floor((Date.now() - Date.parse(activeEntry.started_at)) / 1000)
    setElapsed(initial)

    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - Date.parse(activeEntry.started_at)) / 1000))
    }, 1000)
    return () => clearInterval(id)
  }, [activeEntry])

  if (!activeEntry) {
    return (
      <button className="timer-btn timer-btn--start" data-testid="timer-start-btn" onClick={onStart}>
        Start
      </button>
    )
  }

  return (
    <div className="timer-active">
      <span className="timer-elapsed" data-testid="timer-elapsed">{formatElapsed(elapsed)}</span>
      <button
        className="timer-btn timer-btn--stop"
        data-testid="timer-stop-btn"
        onClick={() => onStop(activeEntry.id)}
      >
        Stop
      </button>
    </div>
  )
}

export default TimerButton
