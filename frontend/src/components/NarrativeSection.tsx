import React from 'react'
import { Sparkle, Warning, Clock } from '@phosphor-icons/react'
import type { ReviewStatus } from '../types/weeklyReview'

interface NarrativeSectionProps {
  narrative: string | null
  status: ReviewStatus
}

function NarrativeSection({ narrative, status }: NarrativeSectionProps): React.JSX.Element {
  if (status === 'generating') {
    return (
      <div data-testid="narrative-generating" className="ai-block narrative-state">
        <div className="ai-label">
          <Sparkle size={12} weight="fill" />
          AI NARRATIVE
        </div>
        <div className="narrative-generating-text">
          <span className="narrative-dot" />
          Generating your weekly review…
        </div>
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div data-testid="narrative-error" className="narrative-state narrative-state--error">
        <Warning size={16} color="var(--danger)" />
        Review generation failed. Try regenerating.
      </div>
    )
  }

  if (status === 'pending') {
    return (
      <div data-testid="narrative-pending" className="ai-block narrative-state">
        <div className="ai-label">
          <Clock size={12} weight="fill" />
          AI NARRATIVE
        </div>
        <p style={{ color: 'var(--text-3)', fontSize: 13 }}>
          No review yet. Generate one to get started.
        </p>
      </div>
    )
  }

  if (!narrative) {
    return (
      <div data-testid="narrative-empty" className="ai-block narrative-state">
        <p style={{ color: 'var(--text-3)', fontSize: 13 }}>
          Review complete but no narrative available.
        </p>
      </div>
    )
  }

  return (
    <div className="ai-block" data-testid="narrative-content">
      <div className="ai-label">
        <Sparkle size={12} weight="fill" />
        AI NARRATIVE
      </div>
      <article className="narrative-body">{narrative}</article>
    </div>
  )
}

export default NarrativeSection
