import React from 'react'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'
import { Sparkle } from '@phosphor-icons/react'
import type { JudgeScores } from '../types/weeklyReview'

interface JudgeScoreCardProps {
  scores: JudgeScores | null
}

function JudgeScoreCard({ scores }: JudgeScoreCardProps): React.JSX.Element | null {
  if (!scores) return null

  const data = [
    { dimension: 'Actionability', value: scores.actionability },
    { dimension: 'Accuracy',      value: scores.accuracy },
    { dimension: 'Coherence',     value: scores.coherence },
  ]

  const avg = Math.round((scores.actionability + scores.accuracy + scores.coherence) / 3)

  return (
    <div data-testid="judge-score-card" className="ai-block">
      <div className="ai-label">
        <Sparkle size={11} weight="fill" />
        AI EVALUATION
      </div>

      {/* Score pill summary */}
      <div className="judge-scores-row">
        <div className="judge-score-pill">
          <span className="judge-score-value" data-testid="score-actionability">
            {scores.actionability}
          </span>
          <span className="judge-score-label">Action</span>
        </div>
        <div className="judge-score-pill">
          <span className="judge-score-value" data-testid="score-accuracy">
            {scores.accuracy}
          </span>
          <span className="judge-score-label">Accuracy</span>
        </div>
        <div className="judge-score-pill">
          <span className="judge-score-value" data-testid="score-coherence">
            {scores.coherence}
          </span>
          <span className="judge-score-label">Coherence</span>
        </div>
        <div className="judge-avg">
          <span className="judge-avg-value">{avg}</span>
          <span className="judge-score-label">avg / 10</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 16 }}>
          <PolarGrid stroke="rgba(84,120,255,0.15)" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: 'var(--text-3)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
          />
          <PolarRadiusAxis domain={[0, 10]} tick={false} axisLine={false} />
          <Radar
            dataKey="value"
            stroke="var(--cyan)"
            fill="var(--cyan)"
            fillOpacity={0.18}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default JudgeScoreCard
