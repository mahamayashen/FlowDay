import React from 'react'
import type { ReviewStatus } from '../types/weeklyReview'

interface NarrativeSectionProps {
  narrative: string | null
  status: ReviewStatus
}

function NarrativeSection({ narrative, status }: NarrativeSectionProps): React.JSX.Element {
  if (status === 'generating') {
    return <div data-testid="narrative-generating">Generating your weekly review...</div>
  }

  if (status === 'failed') {
    return <div data-testid="narrative-error">Review generation failed. Try regenerating.</div>
  }

  if (status === 'pending') {
    return <div data-testid="narrative-pending">No review yet. Generate one to get started.</div>
  }

  if (!narrative) {
    return <div data-testid="narrative-empty">Review complete but no narrative available.</div>
  }

  return (
    <article data-testid="narrative-content" style={{ whiteSpace: 'pre-wrap' }}>
      {narrative}
    </article>
  )
}

export default NarrativeSection
