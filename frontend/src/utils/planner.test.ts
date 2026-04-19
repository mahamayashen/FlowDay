import { describe, it, expect } from 'vitest'
import {
  formatHour,
  generateHourSlots,
  hourToPixelOffset,
  pixelToHour,
  getBlockStyle,
} from './planner'

describe('formatHour', () => {
  it('formats whole hours in AM', () => {
    expect(formatHour(8)).toBe('8:00 AM')
    expect(formatHour(0)).toBe('12:00 AM')
    expect(formatHour(11)).toBe('11:00 AM')
  })

  it('formats noon correctly', () => {
    expect(formatHour(12)).toBe('12:00 PM')
  })

  it('formats whole hours in PM', () => {
    expect(formatHour(13)).toBe('1:00 PM')
    expect(formatHour(17)).toBe('5:00 PM')
  })

  it('formats half-hour increments', () => {
    expect(formatHour(9.5)).toBe('9:30 AM')
    expect(formatHour(13.5)).toBe('1:30 PM')
  })
})

describe('generateHourSlots', () => {
  it('generates slots from start up to (not including) end', () => {
    expect(generateHourSlots(8, 11)).toEqual([8, 9, 10])
  })

  it('generates single-hour range', () => {
    expect(generateHourSlots(9, 10)).toEqual([9])
  })

  it('generates full work day', () => {
    const slots = generateHourSlots(8, 18)
    expect(slots).toHaveLength(10)
    expect(slots[0]).toBe(8)
    expect(slots[9]).toBe(17)
  })
})

describe('hourToPixelOffset', () => {
  it('returns 0 for grid start hour', () => {
    expect(hourToPixelOffset(8, 8, 60)).toBe(0)
  })

  it('returns hourHeight for one hour past start', () => {
    expect(hourToPixelOffset(9, 8, 60)).toBe(60)
  })

  it('returns half hourHeight for 30-minute offset', () => {
    expect(hourToPixelOffset(8.5, 8, 60)).toBe(30)
  })

  it('works with custom hourHeight', () => {
    expect(hourToPixelOffset(10, 8, 80)).toBe(160)
  })
})

describe('pixelToHour', () => {
  it('converts 0 pixels to startHour', () => {
    expect(pixelToHour(0, 8, 60)).toBe(8)
  })

  it('converts one full hourHeight to startHour + 1', () => {
    expect(pixelToHour(60, 8, 60)).toBe(9)
  })

  it('snaps to nearest 0.25 (quarter hour)', () => {
    // 45px / 60 = 0.75 hours -> 8.75
    expect(pixelToHour(45, 8, 60)).toBe(8.75)
    // 50px / 60 = 0.833 -> nearest 0.25 = 0.75 -> 8.75
    expect(pixelToHour(50, 8, 60)).toBe(8.75)
  })
})

describe('getBlockStyle', () => {
  it('returns top=0 and height=hourHeight for a 1-hour block starting at gridStart', () => {
    const style = getBlockStyle({ start_hour: 8, end_hour: 9 }, 8, 60)
    expect(style.top).toBe(0)
    expect(style.height).toBe(60)
  })

  it('returns correct top for block starting after gridStart', () => {
    const style = getBlockStyle({ start_hour: 10, end_hour: 11.5 }, 8, 60)
    expect(style.top).toBe(120)
    expect(style.height).toBe(90)
  })
})
