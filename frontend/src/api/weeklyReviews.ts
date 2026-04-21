import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import type { WeeklyReview, JudgeScores, ReviewStatus } from '../types/weeklyReview'

export const WEEKLY_REVIEW_KEYS = {
  list: () => ['weekly-reviews'] as const,
  // Kept for backwards-compat — both hooks share the list cache, so "current"
  // is derived via `select` rather than its own endpoint.
  current: (weekStart: string) => ['weekly-reviews', 'current', weekStart] as const,
}

// ── Normalizers ─────────────────────────────────────────────────────
// The backend stores `scores_json` as the raw `JudgeResult.model_dump()`:
//   { actionability_score, accuracy_score, coherence_score, overall_score, feedback }
// The frontend surface area is simpler. Translate at the edge.

interface RawJudgeScores {
  actionability_score?: number
  accuracy_score?: number
  coherence_score?: number
  // fallbacks if the API ever drops `_score`
  actionability?: number
  accuracy?: number
  coherence?: number
}

function normalizeScores(raw: unknown): JudgeScores | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as RawJudgeScores
  const a = r.actionability_score ?? r.actionability
  const b = r.accuracy_score ?? r.accuracy
  const c = r.coherence_score ?? r.coherence
  if (typeof a !== 'number' || typeof b !== 'number' || typeof c !== 'number') return null
  return { actionability: a, accuracy: b, coherence: c }
}

interface RawWeeklyReview {
  id: string
  user_id: string
  week_start: string
  status: ReviewStatus
  narrative: string | null
  insights_json: Record<string, unknown> | null
  scores_json: Record<string, unknown> | null
  agent_metadata_json?: Record<string, unknown> | null
  created_at: string
}

function normalizeReview(raw: RawWeeklyReview): WeeklyReview {
  return {
    id: raw.id,
    user_id: raw.user_id,
    week_start: raw.week_start,
    status: raw.status,
    narrative: raw.narrative,
    insights_json: raw.insights_json,
    scores_json: normalizeScores(raw.scores_json),
    created_at: raw.created_at,
  }
}

// ── Network ─────────────────────────────────────────────────────────

async function fetchAllReviews(): Promise<WeeklyReview[]> {
  const res = await apiClient.get('/weekly-reviews')
  if (!res.ok) throw new Error('Failed to fetch weekly reviews')
  const list = (await res.json()) as RawWeeklyReview[]
  return list.map(normalizeReview)
}

async function generateWeeklyReview(weekStart: string): Promise<WeeklyReview> {
  // Backend takes week_start as a query param, not a JSON body.
  // POST is synchronous — it blocks 10–30s while the A→B→C→D pipeline runs
  // and returns the completed review (or the row flipped to status=failed).
  const res = await apiClient.post(
    `/weekly-reviews/generate?week_start=${encodeURIComponent(weekStart)}`,
  )
  if (!res.ok) throw new Error('Failed to generate weekly review')
  const raw = (await res.json()) as RawWeeklyReview
  return normalizeReview(raw)
}

// ── Hooks ───────────────────────────────────────────────────────────

export function useWeeklyReview(weekStart: string) {
  return useQuery({
    queryKey: WEEKLY_REVIEW_KEYS.list(),
    queryFn: fetchAllReviews,
    enabled: Boolean(weekStart),
    staleTime: 0,
    select: (list): WeeklyReview | undefined =>
      list.find((r) => r.week_start === weekStart),
  })
}

export function useWeeklyReviewHistory(limit = 10) {
  return useQuery({
    queryKey: WEEKLY_REVIEW_KEYS.list(),
    queryFn: fetchAllReviews,
    select: (list) => list.slice(0, limit),
  })
}

export function useGenerateWeeklyReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (weekStart: string) => generateWeeklyReview(weekStart),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: WEEKLY_REVIEW_KEYS.list() })
    },
  })
}
