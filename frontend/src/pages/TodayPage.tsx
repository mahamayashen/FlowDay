import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Play, Pause, CalendarPlus, Sparkle } from '@phosphor-icons/react'
import {
  mockBlocksToday,
  mockTimeEntriesToday,
  mockDailyNarrative,
  findTask,
  projectForTask,
  TODAY_ISO,
} from '../mocks/data'
import type { ScheduleBlock } from '../types/scheduleBlock'
import './TodayPage.css'

const WORK_START = 8
const WORK_END = 19
const HOUR_PX = 68 // timeline row height

function formatHour(h: number): string {
  const whole = Math.floor(h)
  const mins = Math.round((h - whole) * 60)
  const display = whole === 0 ? 12 : whole > 12 ? whole - 12 : whole
  const ampm = whole >= 12 ? 'PM' : 'AM'
  return mins === 0
    ? `${display}:00 ${ampm}`
    : `${display}:${String(mins).padStart(2, '0')} ${ampm}`
}

function useNow(): Date {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30_000)
    return () => clearInterval(t)
  }, [])
  return now
}

function TodayPage(): React.JSX.Element {
  const now = useNow()
  const nowHour = now.getHours() + now.getMinutes() / 60
  const [activeBlockId, setActiveBlockId] = useState<string | null>(null)

  const currentBlock = useMemo(
    () => mockBlocksToday.find((b) => nowHour >= b.start_hour && nowHour < b.end_hour),
    [nowHour],
  )

  const totalPlanned = useMemo(
    () => mockBlocksToday.reduce((acc, b) => acc + (b.end_hour - b.start_hour), 0),
    [],
  )
  const totalActual = useMemo(
    () => mockTimeEntriesToday.reduce((acc, t) => acc + t.duration_minutes / 60, 0),
    [],
  )
  const progressPct = Math.min(100, Math.round((totalActual / totalPlanned) * 100))

  function handleStart(block: ScheduleBlock): void {
    setActiveBlockId((prev) => (prev === block.id ? null : block.id))
  }

  const nowTop = (nowHour - WORK_START) * HOUR_PX
  const timelineHeight = (WORK_END - WORK_START) * HOUR_PX

  return (
    <main className="today-page" data-testid="page-today">
      <header className="today-header">
        <div>
          <p className="today-eyebrow">TODAY · {new Date(TODAY_ISO + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</p>
          <h1 className="today-title">
            {currentBlock ? `In flow — ${findTask(currentBlock.task_id)?.title}` : 'No active block right now'}
          </h1>
        </div>
        <div className="today-stats">
          <div className="stat-pill">
            <span className="stat-pill-label">Planned</span>
            <span className="stat-pill-value">{totalPlanned.toFixed(1)}h</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-label">Tracked</span>
            <span className="stat-pill-value stat-pill-value--accent">{totalActual.toFixed(1)}h</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-label">Progress</span>
            <span className="stat-pill-value">{progressPct}%</span>
          </div>
        </div>
      </header>

      <div className="today-progress-bar">
        <div className="today-progress-fill" style={{ width: `${progressPct}%` }} />
      </div>

      <div className="today-body">
        <section className="today-timeline-wrap">
          <div className="today-timeline" style={{ height: timelineHeight }}>
            {/* hour labels + grid lines */}
            {Array.from({ length: WORK_END - WORK_START + 1 }, (_, i) => WORK_START + i).map((h) => (
              <div
                key={h}
                className="timeline-row"
                style={{ top: (h - WORK_START) * HOUR_PX }}
              >
                <span className="timeline-hour-label">{formatHour(h)}</span>
                <div className="timeline-hour-line" />
              </div>
            ))}

            {/* now indicator */}
            {nowHour >= WORK_START && nowHour <= WORK_END && (
              <div className="now-indicator" style={{ top: nowTop }}>
                <span className="now-label">{formatHour(nowHour)}</span>
                <span className="now-line" />
              </div>
            )}

            {/* blocks */}
            {mockBlocksToday.map((block) => {
              const task = findTask(block.task_id)
              const project = projectForTask(block.task_id)
              const top = (block.start_hour - WORK_START) * HOUR_PX
              const height = (block.end_hour - block.start_hour) * HOUR_PX
              const isPast = block.end_hour <= nowHour
              const isNow = nowHour >= block.start_hour && nowHour < block.end_hour
              const isActive = activeBlockId === block.id
              const isCalendar = block.source === 'google_calendar'

              return (
                <div
                  key={block.id}
                  className={`today-block${isNow ? ' today-block--now' : ''}${isPast ? ' today-block--past' : ''}${isActive ? ' today-block--active' : ''}${isCalendar ? ' today-block--calendar' : ''}`}
                  style={{
                    top,
                    height,
                    borderLeftColor: isCalendar ? '#8B9BC8' : project?.color ?? '#5478FF',
                  }}
                  data-testid="today-block"
                >
                  <div className="today-block-head">
                    <span className="today-block-project" style={{ color: project?.color }}>
                      {isCalendar ? 'CALENDAR' : project?.name.toUpperCase()}
                    </span>
                    <span className="today-block-time">
                      {formatHour(block.start_hour)} – {formatHour(block.end_hour)}
                    </span>
                  </div>
                  <div className="today-block-title">
                    {isCalendar ? 'Team standup' : task?.title ?? 'Untitled'}
                  </div>
                  {!isCalendar && !isPast && (
                    <button
                      className={`today-block-start${isActive ? ' today-block-start--running' : ''}`}
                      onClick={() => handleStart(block)}
                      data-testid="btn-start-block"
                    >
                      {isActive ? <Pause size={14} weight="fill" /> : <Play size={14} weight="fill" />}
                      {isActive ? 'Running' : 'Start'}
                    </button>
                  )}
                  {isPast && (
                    <span className="today-block-done">Tracked</span>
                  )}
                </div>
              )
            })}
          </div>
        </section>

        <aside className="today-sidebar">
          <div className="ai-blurb">
            <div className="ai-blurb-head">
              <Sparkle size={16} color="var(--cyan)" weight="fill" />
              <span>AI coach · preview</span>
            </div>
            <p className="ai-blurb-body">{mockDailyNarrative}</p>
            <Link to="/review" className="ai-blurb-link">Open full review →</Link>
          </div>

          <div className="today-quickstart">
            <h3 className="qs-title">Unplanned? Start ad-hoc timer</h3>
            <button className="qs-btn">
              <Play size={14} weight="fill" />
              Start without a block
            </button>
          </div>

          <div className="today-quickstart">
            <h3 className="qs-title">Need to replan?</h3>
            <Link to="/plan" className="qs-btn qs-btn--outline">
              <CalendarPlus size={14} />
              Open Plan
            </Link>
          </div>
        </aside>
      </div>
    </main>
  )
}

export default TodayPage
