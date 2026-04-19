import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import JudgeScoreCard from './JudgeScoreCard'
import type { JudgeScores } from '../types/weeklyReview'

vi.stubGlobal('ResizeObserver', class {
  observe() {}
  unobserve() {}
  disconnect() {}
})

const mockScores: JudgeScores = {
  actionability: 85,
  accuracy: 72,
  coherence: 91,
}

describe('JudgeScoreCard', () => {
  it('shows nothing when scores are null', () => {
    const { container } = render(<JudgeScoreCard scores={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders actionability score', () => {
    render(<JudgeScoreCard scores={mockScores} />)
    expect(screen.getByTestId('score-actionability')).toHaveTextContent('85')
  })

  it('renders accuracy score', () => {
    render(<JudgeScoreCard scores={mockScores} />)
    expect(screen.getByTestId('score-accuracy')).toHaveTextContent('72')
  })

  it('renders coherence score', () => {
    render(<JudgeScoreCard scores={mockScores} />)
    expect(screen.getByTestId('score-coherence')).toHaveTextContent('91')
  })

  it('renders the score card container', () => {
    render(<JudgeScoreCard scores={mockScores} />)
    expect(screen.getByTestId('judge-score-card')).toBeInTheDocument()
  })
})
