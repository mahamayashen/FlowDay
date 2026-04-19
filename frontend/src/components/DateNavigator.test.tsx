import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DateNavigator from './DateNavigator'

const defaultProps = {
  selectedDate: '2026-04-18',
  onPrevDay: vi.fn(),
  onNextDay: vi.fn(),
  onDateChange: vi.fn(),
}

describe('DateNavigator', () => {
  it('displays the formatted selected date', () => {
    render(<DateNavigator {...defaultProps} />)
    expect(screen.getByTestId('selected-date-label')).toHaveTextContent('April 18, 2026')
  })

  it('calls onPrevDay when prev button is clicked', () => {
    const onPrevDay = vi.fn()
    render(<DateNavigator {...defaultProps} onPrevDay={onPrevDay} />)
    fireEvent.click(screen.getByTestId('prev-day-btn'))
    expect(onPrevDay).toHaveBeenCalledOnce()
  })

  it('calls onNextDay when next button is clicked', () => {
    const onNextDay = vi.fn()
    render(<DateNavigator {...defaultProps} onNextDay={onNextDay} />)
    fireEvent.click(screen.getByTestId('next-day-btn'))
    expect(onNextDay).toHaveBeenCalledOnce()
  })

  it('renders a date input with the current date value', () => {
    render(<DateNavigator {...defaultProps} />)
    const input = screen.getByTestId('date-picker-input')
    expect(input).toHaveAttribute('type', 'date')
    expect(input).toHaveValue('2026-04-18')
  })

  it('calls onDateChange when date input changes', () => {
    const onDateChange = vi.fn()
    render(<DateNavigator {...defaultProps} onDateChange={onDateChange} />)
    fireEvent.change(screen.getByTestId('date-picker-input'), {
      target: { value: '2026-05-01' },
    })
    expect(onDateChange).toHaveBeenCalledWith('2026-05-01')
  })
})
