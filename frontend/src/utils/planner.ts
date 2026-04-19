export const HOUR_HEIGHT = 60 // pixels per hour

export function formatHour(hour: number): string {
  const wholeHour = Math.floor(hour)
  const minutes = Math.round((hour - wholeHour) * 60)
  const period = wholeHour < 12 ? 'AM' : 'PM'
  const displayHour = wholeHour % 12 === 0 ? 12 : wholeHour % 12
  return `${displayHour}:${minutes.toString().padStart(2, '0')} ${period}`
}

export function generateHourSlots(start: number, end: number): number[] {
  const slots: number[] = []
  for (let h = start; h < end; h++) {
    slots.push(h)
  }
  return slots
}

export function hourToPixelOffset(hour: number, startHour: number, hourHeight: number): number {
  return (hour - startHour) * hourHeight
}

export function pixelToHour(pixelY: number, startHour: number, hourHeight: number): number {
  const rawHour = startHour + pixelY / hourHeight
  return Math.round(rawHour * 4) / 4 // snap to nearest 0.25
}

export function getBlockStyle(
  block: { start_hour: number; end_hour: number },
  gridStartHour: number,
  hourHeight: number,
): { top: number; height: number } {
  return {
    top: hourToPixelOffset(block.start_hour, gridStartHour, hourHeight),
    height: (block.end_hour - block.start_hour) * hourHeight,
  }
}
