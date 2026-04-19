export type ReviewStatus = 'pending' | 'generating' | 'complete' | 'failed'

export interface JudgeScores {
  actionability: number
  accuracy: number
  coherence: number
}

export interface WeeklyReview {
  id: string
  user_id: string
  week_start: string
  narrative: string | null
  insights_json: Record<string, unknown> | null
  scores_json: JudgeScores | null
  status: ReviewStatus
  created_at: string
}
