import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { Play, Pause, CalendarPlus, Sparkle } from '@phosphor-icons/react'
import { useScheduleBlocks } from '../api/scheduleBlocks'
import { useProjects } from '../api/projects'
import { fetchProjectTasks, TASK_KEYS } from '../api/tasks'
import { usePlannedVsActual } from '../api/analytics'
import { useActiveTimer, useStartTimer, useStopTimer } from '../api/timeEntries'
import { useTimerStore } from '../stores/timerStore'
import { formatLocalDate } from '../utils/reviewUtils'
import type { Project } from '../types/project'
import type { Task } from '../types/task'
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
  const today = useMemo(() => formatLocalDate(now), [now])
  const nowHour = now.getHours() + now.getMinutes() / 60

  // ── Real data ──────────────────────────────────────
  const { data: blocks = [] } = useScheduleBlocks(today)
  const { data: projects = [] } = useProjects()
  const { data: plannedVsActual } = usePlannedVsActual(today)
  const { data: activeEntry } = useActiveTimer()

  const startTimer = useStartTimer()
  const stopTimer = useStopTimer()
  const startTick = useTimerStore((s) => s.startTick)
  const stopTick = useTimerStore((s) => s.stopTick)

  // Fetch tasks for every project so we can resolve block.task_id → task title.
  // Same pattern as PlannerPage.
  const taskQueries = useQueries({
    queries: projects.map((p: Project) => ({
      queryKey: TASK_KEYS.byProject(p.id),
      queryFn: () => fetchProjectTasks(p.id),
    })),
  })

  const taskMap = useMemo<Map<string, Task>>(() => {
    const map = new Map<string, Task>()
    for (const q of taskQueries) {
      for (const t of q.data ?? []) {
        map.set(t.id, t)
      }
    }
    return map
  }, [taskQueries])

  const projectMap = useMemo<Map<string, Project>>(() => {
    const map = new Map<string, Project>()
    for (const p of projects) map.set(p.id, p)
    return map
  }, [projects])

  // ── Derived UI state ───────────────────────────────
  const currentBlock = useMemo(
    () => blocks.find((b) => nowHour >= b.start_hour && nowHour < b.end_hour),
    [blocks, nowHour],
  )

  const totalPlanned = plannedVsActual?.summary.total_planned_hours ?? 0
  const totalActual = plannedVsActual?.summary.total_actual_hours ?? 0
  const progressPct =
    totalPlanned === 0 ? 0 : Math.min(100, Math.round((totalActual / totalPlanned) * 100))

  const currentTask = currentBlock ? taskMap.get(currentBlock.task_id) : undefined

  // ── Timer handlers ─────────────────────────────────
  function handleStartBlock(taskId: string): void {
    startTimer.mutate(
      { task_id: taskId },
      {
        onSuccess: (entry) => startTick(entry.id, entry.task_id),
      },
    )
  }

  function handleStopActive(): void {
    if (!activeEntry) return
    stopTimer.mutate(activeEntry.id, { onSuccess: () => stopTick() })
  }

  const nowTop = (nowHour - WORK_START) * HOUR_PX
  const timelineHeight = (WORK_END - WORK_START) * HOUR_PX

  return (
    <main className="today-page" data-testid="page-today">
      <header className="today-header">
        <div>
          <p className="today-eyebrow">
            TODAY ·{' '}
            {new Date(today + 'T00:00:00').toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'short',
              day: 'numeric',
            })}
          </p>
          <h1 className="today-title">
            {currentTask
              ? `In flow — ${currentTask.title}`
              : currentBlock
                ? 'In flow'
                : 'No active block right now'}
          </h1>
        </div>
        <div className="today-stats">
          <div className="stat-pill">
            <span className="stat-pill-label">Planned</span>
            <span className="stat-pill-value">{totalPlanned.toFixed(1)}h</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-label">Tracked</span>
            <span className="stat-pill-value stat-pill-value--accent">
              {totalActual.toFixed(1)}h
            </span>
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
                className="today-timeline-row"
                style={{ top: (h - WORK_START) * HOUR_PX }}
              >
                <span className="today-timeline-hour-label">{formatHour(h)}</span>
                <div className="today-timeline-hour-line" />
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
            {blocks.length === 0 && (
              <div className="today-empty-timeline" data-testid="today-empty">
                Nothing scheduled for today. <Link to="/plan">Open Plan →</Link>
              </div>
            )}

            {blocks.map((block) => {
              const task = taskMap.get(block.task_id)
              const project = task ? projectMap.get(task.project_id) : undefined
              const top = (block.start_hour - WORK_START) * HOUR_PX
              const height = (block.end_hour - block.start_hour) * HOUR_PX
              const isPast = block.end_hour <= nowHour
              const isNow = nowHour >= block.start_hour && nowHour < block.end_hour
              const isActiveTimer = activeEntry?.task_id === block.task_id
              const isCalendar = block.source === 'google_calendar'

              return (
                <div
                  key={block.id}
                  className={`today-block${isNow ? ' today-block--now' : ''}${
                    isPast ? ' today-block--past' : ''
                  }${isActiveTimer ? ' today-block--active' : ''}${
                    isCalendar ? ' today-block--calendar' : ''
                  }`}
                  style={{
                    top,
                    height,
                    borderLeftColor: isCalendar ? '#8B9BC8' : project?.color ?? '#5478FF',
                  }}
                  data-testid="today-block"
                >
                  <div className="today-block-head">
                    <span className="today-block-project" style={{ color: project?.color }}>
                      {isCalendar ? 'CALENDAR' : project?.name.toUpperCase() ?? 'TASK'}
                    </span>
                    <span className="today-block-time">
                      {formatHour(block.start_hour)} – {formatHour(block.end_hour)}
                    </span>
                  </div>
                  <div className="today-block-title">
                    {isCalendar ? 'Calendar event' : task?.title ?? 'Untitled task'}
                  </div>
                  {!isCalendar && !isPast && (
                    <button
                      className={`today-block-start${
                        isActiveTimer ? ' today-block-start--running' : ''
                      }`}
                      onClick={() =>
                        isActiveTimer ? handleStopActive() : handleStartBlock(block.task_id)
                      }
                      disabled={startTimer.isPending || stopTimer.isPending}
                      data-testid="btn-start-block"
                    >
                      {isActiveTimer ? (
                        <Pause size={14} weight="fill" />
                      ) : (
                        <Play size={14} weight="fill" />
                      )}
                      {isActiveTimer ? 'Running' : 'Start'}
                    </button>
                  )}
                  {isPast && <span className="today-block-done">Tracked</span>}
                </div>
              )
            })}
          </div>
        </section>

        <aside className="today-sidebar">
          <div className="ai-blurb">
            <div className="ai-blurb-head">
              <Sparkle size={16} color="var(--cyan)" weight="fill" />
              <span>AI coach</span>
            </div>
            <p className="ai-blurb-body">
              Your AI weekly review digests the past 7 days and surfaces patterns — open it
              at the end of the week to see how you really spent your time.
            </p>
            <Link to="/weekly" className="ai-blurb-link">
              Open weekly review →
            </Link>
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
