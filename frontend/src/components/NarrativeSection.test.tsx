import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import NarrativeSection from './NarrativeSection'
import type { ReviewStatus } from '../types/weeklyReview'

describe('NarrativeSection', () => {
  it('shows generating state', () => {
    render(<NarrativeSection narrative={null} status="generating" />)
    expect(screen.getByTestId('narrative-generating')).toBeInTheDocument()
  })

  it('shows pending state', () => {
    render(<NarrativeSection narrative={null} status="pending" />)
    expect(screen.getByTestId('narrative-pending')).toBeInTheDocument()
  })

  it('shows failed state', () => {
    render(<NarrativeSection narrative={null} status="failed" />)
    expect(screen.getByTestId('narrative-error')).toBeInTheDocument()
  })

  it('shows narrative content when complete', () => {
    render(<NarrativeSection narrative="Great week of productivity!" status="complete" />)
    expect(screen.getByTestId('narrative-content')).toHaveTextContent('Great week of productivity!')
  })

  it('shows empty state when complete but narrative is null', () => {
    render(<NarrativeSection narrative={null} status={'complete' as ReviewStatus} />)
    expect(screen.getByTestId('narrative-empty')).toBeInTheDocument()
  })
})
