import type { Project } from '../types/project'
import type { Task } from '../types/task'
import type { ScheduleBlock } from '../types/scheduleBlock'

// ──────────────────────────────────────────────────────────────
// Central mock data for the v2 shell preview.
// Swap individual arrays for real API hooks later.
// ──────────────────────────────────────────────────────────────

export const MOCK_USER_ID = 'usr-demo'

// Today's ISO date, used by Today + Review pages
export const TODAY_ISO = new Date().toISOString().slice(0, 10)
export const YESTERDAY_ISO = (() => {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().slice(0, 10)
})()
export const TOMORROW_ISO = (() => {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
})()

// ── Projects ───────────────────────────────────────────────────
export const mockProjects: Project[] = [
  {
    id: 'proj-acme',
    user_id: MOCK_USER_ID,
    name: 'Acme Website Redesign',
    color: '#FFDE42',
    client_name: 'Acme Corp',
    hourly_rate: '120.00',
    status: 'active',
    created_at: '2026-04-01T09:00:00Z',
  },
  {
    id: 'proj-tutoring',
    user_id: MOCK_USER_ID,
    name: 'Tutoring',
    color: '#53CBF3',
    client_name: null,
    hourly_rate: '85.00',
    status: 'active',
    created_at: '2026-03-15T09:00:00Z',
  },
  {
    id: 'proj-personal',
    user_id: MOCK_USER_ID,
    name: 'Personal — Writing',
    color: '#5478FF',
    client_name: null,
    hourly_rate: null,
    status: 'active',
    created_at: '2026-02-20T09:00:00Z',
  },
  {
    id: 'proj-internal',
    user_id: MOCK_USER_ID,
    name: 'FlowDay (self-hosted)',
    color: '#34D399',
    client_name: 'Self',
    hourly_rate: null,
    status: 'active',
    created_at: '2026-01-10T09:00:00Z',
  },
]

// ── Tasks ──────────────────────────────────────────────────────
export const mockTasks: Task[] = [
  // Acme
  {
    id: 'task-hero',
    project_id: 'proj-acme',
    title: 'Design hero section v3',
    description: 'Iterate on gradient + new headline copy',
    estimate_minutes: 120,
    priority: 'high',
    status: 'in_progress',
    due_date: TOMORROW_ISO,
    created_at: '2026-04-15T09:00:00Z',
    completed_at: null,
  },
  {
    id: 'task-api',
    project_id: 'proj-acme',
    title: 'Wire up contact form API',
    description: 'POST /contact with validation',
    estimate_minutes: 90,
    priority: 'medium',
    status: 'todo',
    due_date: TOMORROW_ISO,
    created_at: '2026-04-16T09:00:00Z',
    completed_at: null,
  },
  {
    id: 'task-deploy',
    project_id: 'proj-acme',
    title: 'Deploy staging build',
    description: null,
    estimate_minutes: 30,
    priority: 'medium',
    status: 'todo',
    due_date: null,
    created_at: '2026-04-18T09:00:00Z',
    completed_at: null,
  },
  // Tutoring
  {
    id: 'task-weekly',
    project_id: 'proj-tutoring',
    title: 'Weekly session prep — calculus',
    description: 'Cover integration by parts',
    estimate_minutes: 60,
    priority: 'medium',
    status: 'todo',
    due_date: TODAY_ISO,
    created_at: '2026-04-18T09:00:00Z',
    completed_at: null,
  },
  // Personal
  {
    id: 'task-essay',
    project_id: 'proj-personal',
    title: 'Draft newsletter — April edition',
    description: null,
    estimate_minutes: 90,
    priority: 'low',
    status: 'todo',
    due_date: null,
    created_at: '2026-04-12T09:00:00Z',
    completed_at: null,
  },
  // Internal
  {
    id: 'task-retro',
    project_id: 'proj-internal',
    title: 'Ship v2 product rebuild',
    description: 'Restructure pages, hook up AI pipeline',
    estimate_minutes: 240,
    priority: 'urgent',
    status: 'in_progress',
    due_date: TOMORROW_ISO,
    created_at: '2026-04-19T09:00:00Z',
    completed_at: null,
  },
]

// ── Schedule Blocks (today's plan) ─────────────────────────────
// Hours in 24h float; e.g. 9.5 = 9:30am
export const mockBlocksToday: ScheduleBlock[] = [
  {
    id: 'blk-1',
    task_id: 'task-retro',
    date: TODAY_ISO,
    start_hour: 9,
    end_hour: 11,
    source: 'manual',
    created_at: '2026-04-20T08:00:00Z',
  },
  {
    id: 'blk-standup',
    task_id: 'task-retro',
    date: TODAY_ISO,
    start_hour: 11,
    end_hour: 11.5,
    source: 'google_calendar',
    created_at: '2026-04-20T08:00:00Z',
  },
  {
    id: 'blk-2',
    task_id: 'task-hero',
    date: TODAY_ISO,
    start_hour: 13,
    end_hour: 15,
    source: 'manual',
    created_at: '2026-04-20T08:00:00Z',
  },
  {
    id: 'blk-3',
    task_id: 'task-weekly',
    date: TODAY_ISO,
    start_hour: 15.5,
    end_hour: 16.5,
    source: 'manual',
    created_at: '2026-04-20T08:00:00Z',
  },
  {
    id: 'blk-4',
    task_id: 'task-api',
    date: TODAY_ISO,
    start_hour: 16.75,
    end_hour: 18,
    source: 'manual',
    created_at: '2026-04-20T08:00:00Z',
  },
]

// ── "Actual" time entries for Review page ─────────────────────
// Mirrors today's plan but with drift, to make planned-vs-actual meaningful
export interface MockTimeEntry {
  id: string
  task_id: string
  started_at: string  // ISO
  ended_at: string | null
  duration_minutes: number
}

function mkEntry(id: string, task_id: string, startH: number, endH: number): MockTimeEntry {
  const d = new Date()
  const s = new Date(d)
  s.setHours(Math.floor(startH), Math.round((startH % 1) * 60), 0, 0)
  const e = new Date(d)
  e.setHours(Math.floor(endH), Math.round((endH % 1) * 60), 0, 0)
  return {
    id,
    task_id,
    started_at: s.toISOString(),
    ended_at: e.toISOString(),
    duration_minutes: Math.round((endH - startH) * 60),
  }
}

export const mockTimeEntriesToday: MockTimeEntry[] = [
  mkEntry('te-1', 'task-retro', 9.25, 10.75),          // late start, early end
  mkEntry('te-2', 'task-retro', 11, 11.5),              // standup ran long
  mkEntry('te-3', 'task-hero', 13.1, 14.2),             // cut short
  // 15.5–16.5 tutoring: skipped entirely
  mkEntry('te-4', 'task-api', 16.8, 17.9),
]

// ── AI mock outputs ───────────────────────────────────────────
export const mockDailyNarrative = `You shipped ~4h of deep work today across three projects — strong, but shy of your 6h plan. The hero redesign block lost 50min to an unplanned standup. You skipped the tutoring prep entirely; it's now blocking tomorrow. Tomorrow's top priority: protect the 3pm slot or reschedule it.`

export const mockWeeklyNarrative = `This week you invested 28 focused hours — 12% above your rolling 4-week average. The Acme redesign absorbed 62% of that, which matches your stated priority. However, three consecutive afternoon Acme blocks slipped by 20+ minutes each, suggesting your real-world focus ceiling on heavy design work is closer to 90 minutes than the 120 you've been planning.\n\nYour highest-leverage moment this week was Tuesday morning: four uninterrupted hours on the contact-form API, matching the plan within 5 minutes. The common thread with your best blocks is a clean calendar the morning-of and no standing meetings before 11am. Consider making that a rule.\n\nGoing into next week: tutoring prep was skipped twice and is now a reliability risk. Either lock it into a recurring Monday 4pm slot or drop the commitment — the current pattern damages your credibility with the client.`

export const mockJudgeScores = {
  actionability: 87,
  accuracy: 91,
  coherence: 89,
}

export const mockScoreTrend = [
  { week: '2026-03-16', actionability: 72, accuracy: 80, coherence: 78 },
  { week: '2026-03-23', actionability: 75, accuracy: 82, coherence: 81 },
  { week: '2026-03-30', actionability: 81, accuracy: 85, coherence: 84 },
  { week: '2026-04-06', actionability: 83, accuracy: 88, coherence: 86 },
  { week: '2026-04-13', actionability: 85, accuracy: 90, coherence: 88 },
  { week: '2026-04-20', actionability: 87, accuracy: 91, coherence: 89 },
]

export const mockReviewHistory = [
  { id: 'rv-1', week_start: '2026-04-13', generated_at: '2026-04-19T20:00:00Z', avg_score: 87.7 },
  { id: 'rv-2', week_start: '2026-04-06', generated_at: '2026-04-12T20:00:00Z', avg_score: 85.6 },
  { id: 'rv-3', week_start: '2026-03-30', generated_at: '2026-04-05T20:00:00Z', avg_score: 83.3 },
  { id: 'rv-4', week_start: '2026-03-23', generated_at: '2026-03-29T20:00:00Z', avg_score: 79.3 },
]

// Helper: look up a task by id
export function findTask(id: string): Task | undefined {
  return mockTasks.find((t) => t.id === id)
}

export function findProject(id: string): Project | undefined {
  return mockProjects.find((p) => p.id === id)
}

export function projectForTask(taskId: string): Project | undefined {
  const t = findTask(taskId)
  return t ? findProject(t.project_id) : undefined
}
