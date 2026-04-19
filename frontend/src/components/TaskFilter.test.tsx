import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskFilter from './TaskFilter'
import type { TaskFilterState } from './TaskFilter'

const defaultState: TaskFilterState = {
  priority: 'all',
  status: 'all',
  sortBy: 'due_date_asc',
}

describe('TaskFilter', () => {
  it('renders priority, status and sort-by controls', () => {
    render(<TaskFilter value={defaultState} onChange={vi.fn()} />)
    expect(screen.getByLabelText('Priority')).toBeInTheDocument()
    expect(screen.getByLabelText('Status')).toBeInTheDocument()
    expect(screen.getByLabelText('Sort by')).toBeInTheDocument()
  })

  it('calls onChange with updated priority when priority select changes', () => {
    const onChange = vi.fn()
    render(<TaskFilter value={defaultState} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Priority'), { target: { value: 'high' } })

    expect(onChange).toHaveBeenCalledWith({ ...defaultState, priority: 'high' })
  })

  it('calls onChange with updated status when status select changes', () => {
    const onChange = vi.fn()
    render(<TaskFilter value={defaultState} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'in_progress' } })

    expect(onChange).toHaveBeenCalledWith({ ...defaultState, status: 'in_progress' })
  })

  it('calls onChange with updated sortBy when sort select changes', () => {
    const onChange = vi.fn()
    render(<TaskFilter value={defaultState} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Sort by'), { target: { value: 'priority_desc' } })

    expect(onChange).toHaveBeenCalledWith({ ...defaultState, sortBy: 'priority_desc' })
  })

  it('reflects current filter values in the selects', () => {
    const state: TaskFilterState = { priority: 'urgent', status: 'done', sortBy: 'title_asc' }
    render(<TaskFilter value={state} onChange={vi.fn()} />)

    expect(screen.getByLabelText<HTMLSelectElement>('Priority').value).toBe('urgent')
    expect(screen.getByLabelText<HTMLSelectElement>('Status').value).toBe('done')
    expect(screen.getByLabelText<HTMLSelectElement>('Sort by').value).toBe('title_asc')
  })
})
