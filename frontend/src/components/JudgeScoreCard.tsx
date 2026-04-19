import React from 'react'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'
import type { JudgeScores } from '../types/weeklyReview'

interface JudgeScoreCardProps {
  scores: JudgeScores | null
}

function JudgeScoreCard({ scores }: JudgeScoreCardProps): React.JSX.Element | null {
  if (!scores) return null

  const data = [
    { dimension: 'Actionability', value: scores.actionability },
    { dimension: 'Accuracy', value: scores.accuracy },
    { dimension: 'Coherence', value: scores.coherence },
  ]

  return (
    <div data-testid="judge-score-card">
      <div>
        <span>Actionability: </span>
        <span data-testid="score-actionability">{scores.actionability}</span>
        <span> | Accuracy: </span>
        <span data-testid="score-accuracy">{scores.accuracy}</span>
        <span> | Coherence: </span>
        <span data-testid="score-coherence">{scores.coherence}</span>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="dimension" />
          <PolarRadiusAxis domain={[0, 100]} />
          <Radar dataKey="value" fill="#f59e0b" fillOpacity={0.6} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default JudgeScoreCard
