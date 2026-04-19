export function formatElapsed(seconds: number): string {
  const s = Math.max(0, seconds)
  const mm = Math.floor(s / 60).toString().padStart(2, '0')
  const ss = (s % 60).toString().padStart(2, '0')
  return `${mm}:${ss}`
}
