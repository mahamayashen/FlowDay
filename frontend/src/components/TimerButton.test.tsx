import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import TimerButton from './TimerButton'
import type { TimeEntry } from '../types/timeEntry'

const activeEntry: TimeEntry = {
  id: 'entry-1',
  task_id: 'task-1',
  started_at: new Date(Date.now() - 65_000).toISOString(), // 65 seconds ago
  ended_at: null,
  duration_seconds: null,
  created_at: new Date().toISOString(),
}

describe('TimerButton', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders start button when no active entry', () => {
    render(<TimerButton activeEntry={null} onStart={vi.fn()} onStop={vi.fn()} />)
    expect(screen.getByTestId('timer-start-btn')).toBeInTheDocument()
    expect(screen.getByTestId('timer-start-btn')).toHaveTextContent('Start')
  })

  it('calls onStart when start button is clicked', () => {
    const onStart = vi.fn()
    render(<TimerButton activeEntry={null} onStart={onStart} onStop={vi.fn()} />)
    fireEvent.click(screen.getByTestId('timer-start-btn'))
    expect(onStart).toHaveBeenCalledOnce()
  })

  it('renders stop button and elapsed display when active entry present', () => {
    render(<TimerButton activeEntry={activeEntry} onStart={vi.fn()} onStop={vi.fn()} />)
    expect(screen.getByTestId('timer-stop-btn')).toBeInTheDocument()
    expect(screen.getByTestId('timer-elapsed')).toBeInTheDocument()
  })

  it('calls onStop with entry id when stop button is clicked', () => {
    const onStop = vi.fn()
    render(<TimerButton activeEntry={activeEntry} onStart={vi.fn()} onStop={onStop} />)
    fireEvent.click(screen.getByTestId('timer-stop-btn'))
    expect(onStop).toHaveBeenCalledWith('entry-1')
  })

  it('elapsed display formats seconds as MM:SS', () => {
    // started_at = exactly 65 seconds ago so elapsed starts at 65s → "01:05"
    const entry: TimeEntry = {
      ...activeEntry,
      started_at: new Date(Date.now() - 65_000).toISOString(),
    }
    render(<TimerButton activeEntry={entry} onStart={vi.fn()} onStop={vi.fn()} />)
    // tick one interval so the display renders
    act(() => { vi.advanceTimersByTime(1000) })
    const elapsed = screen.getByTestId('timer-elapsed').textContent ?? ''
    // Should be "01:05" or "01:06" depending on rounding — at minimum contains ":"
    expect(elapsed).toMatch(/^\d{2}:\d{2}$/)
    const [mm, ss] = elapsed.split(':').map(Number)
    expect(mm).toBe(1)
    expect(ss).toBeGreaterThanOrEqual(5)
  })

  it('resumes elapsed from started_at on mount (persistence after refresh)', () => {
    // started_at 30 seconds in the past
    const entry: TimeEntry = {
      ...activeEntry,
      started_at: new Date(Date.now() - 30_000).toISOString(),
    }
    render(<TimerButton activeEntry={entry} onStart={vi.fn()} onStop={vi.fn()} />)
    const elapsed = screen.getByTestId('timer-elapsed').textContent ?? ''
    expect(elapsed).toMatch(/^\d{2}:\d{2}$/)
    const totalSeconds = parseInt(elapsed.split(':')[0]) * 60 + parseInt(elapsed.split(':')[1])
    expect(totalSeconds).toBeGreaterThanOrEqual(30)
  })
})
