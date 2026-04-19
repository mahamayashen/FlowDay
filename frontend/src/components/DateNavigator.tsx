import React from 'react'
import './DateNavigator.css'

interface DateNavigatorProps {
  selectedDate: string
  onPrevDay: () => void
  onNextDay: () => void
  onDateChange: (date: string) => void
}

function formatDateLabel(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

function DateNavigator({
  selectedDate,
  onPrevDay,
  onNextDay,
  onDateChange,
}: DateNavigatorProps): React.JSX.Element {
  return (
    <div className="date-navigator">
      <button
        className="date-nav-btn"
        data-testid="prev-day-btn"
        onClick={onPrevDay}
        aria-label="Previous day"
      >
        ‹
      </button>
      <span className="date-nav-label" data-testid="selected-date-label">
        {formatDateLabel(selectedDate)}
      </span>
      <button
        className="date-nav-btn"
        data-testid="next-day-btn"
        onClick={onNextDay}
        aria-label="Next day"
      >
        ›
      </button>
      <input
        type="date"
        className="date-nav-picker"
        data-testid="date-picker-input"
        value={selectedDate}
        onChange={(e) => onDateChange(e.target.value)}
      />
    </div>
  )
}

export default DateNavigator
