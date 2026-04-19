import { describe, it, expect, beforeEach } from 'vitest'
import { usePlannerStore } from './plannerStore'

function todayString(): string {
  return new Date().toISOString().slice(0, 10)
}

beforeEach(() => {
  usePlannerStore.setState({
    selectedDate: todayString(),
    workHoursStart: 8,
    workHoursEnd: 18,
  })
})

describe('plannerStore', () => {
  it('initializes selectedDate to today', () => {
    expect(usePlannerStore.getState().selectedDate).toBe(todayString())
  })

  it('initializes work hours to 8-18', () => {
    const { workHoursStart, workHoursEnd } = usePlannerStore.getState()
    expect(workHoursStart).toBe(8)
    expect(workHoursEnd).toBe(18)
  })

  it('setSelectedDate sets an arbitrary date', () => {
    usePlannerStore.getState().setSelectedDate('2026-05-01')
    expect(usePlannerStore.getState().selectedDate).toBe('2026-05-01')
  })

  it('goToNextDay increments the date by 1', () => {
    usePlannerStore.getState().setSelectedDate('2026-04-18')
    usePlannerStore.getState().goToNextDay()
    expect(usePlannerStore.getState().selectedDate).toBe('2026-04-19')
  })

  it('goToPrevDay decrements the date by 1', () => {
    usePlannerStore.getState().setSelectedDate('2026-04-18')
    usePlannerStore.getState().goToPrevDay()
    expect(usePlannerStore.getState().selectedDate).toBe('2026-04-17')
  })

  it('goToNextDay crosses month boundary correctly', () => {
    usePlannerStore.getState().setSelectedDate('2026-04-30')
    usePlannerStore.getState().goToNextDay()
    expect(usePlannerStore.getState().selectedDate).toBe('2026-05-01')
  })

  it('setWorkHours updates start and end', () => {
    usePlannerStore.getState().setWorkHours(9, 17)
    expect(usePlannerStore.getState().workHoursStart).toBe(9)
    expect(usePlannerStore.getState().workHoursEnd).toBe(17)
  })
})
