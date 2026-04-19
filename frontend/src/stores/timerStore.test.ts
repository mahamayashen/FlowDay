import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useTimerStore } from './timerStore'

describe('timerStore', () => {
  beforeEach(() => {
    useTimerStore.setState({ activeEntryId: null })
    vi.useFakeTimers()
  })

  afterEach(() => {
    useTimerStore.getState().stopTick()
    vi.useRealTimers()
  })

  it('startTick sets activeEntryId', () => {
    useTimerStore.getState().startTick('entry-1', undefined)
    expect(useTimerStore.getState().activeEntryId).toBe('entry-1')
  })

  it('stopTick clears activeEntryId', () => {
    useTimerStore.getState().startTick('entry-1', undefined)
    useTimerStore.getState().stopTick()
    expect(useTimerStore.getState().activeEntryId).toBeNull()
  })

  it('startTick replaces previous activeEntryId (single-active constraint)', () => {
    useTimerStore.getState().startTick('entry-1', undefined)
    useTimerStore.getState().startTick('entry-2', undefined)
    expect(useTimerStore.getState().activeEntryId).toBe('entry-2')
  })

  it('isTaskTimerActive returns true for the active task', () => {
    useTimerStore.getState().startTick('entry-1', 'task-abc')
    expect(useTimerStore.getState().isTaskTimerActive('task-abc')).toBe(true)
  })

  it('isTaskTimerActive returns false for a different task', () => {
    useTimerStore.getState().startTick('entry-1', 'task-abc')
    expect(useTimerStore.getState().isTaskTimerActive('task-xyz')).toBe(false)
  })
})
