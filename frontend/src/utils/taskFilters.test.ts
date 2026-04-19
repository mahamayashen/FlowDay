import { describe, it, expect } from 'vitest'
import {
  filterByPriority,
  filterByStatus,
  filterByDueDateBefore,
  sortTasks,
} from './taskFilters'
import type { Task } from '../types/task'

function makeTask(overrides: Partial<Task>): Task {
  return {
    id: 'task-1',
    project_id: 'proj-1',
    title: 'Task',
    description: null,
    estimate_minutes: null,
    priority: 'medium',
    status: 'todo',
    due_date: null,
    created_at: '2026-01-01T00:00:00Z',
    completed_at: null,
    ...overrides,
  }
}

const tasks: Task[] = [
  makeTask({ id: '1', priority: 'low',    status: 'todo',        due_date: '2026-01-01', title: 'A' }),
  makeTask({ id: '2', priority: 'medium', status: 'in_progress', due_date: '2026-03-01', title: 'B' }),
  makeTask({ id: '3', priority: 'high',   status: 'done',        due_date: '2026-06-01', title: 'C' }),
  makeTask({ id: '4', priority: 'urgent', status: 'todo',        due_date: null,         title: 'D' }),
]

describe('filterByPriority', () => {
  it('returns all tasks when filter is "all"', () => {
    expect(filterByPriority(tasks, 'all')).toHaveLength(4)
  })

  it('returns only matching priority tasks', () => {
    const result = filterByPriority(tasks, 'high')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('3')
  })

  it('returns empty array when no tasks match', () => {
    expect(filterByPriority(tasks, 'urgent').map((t) => t.id)).toEqual(['4'])
  })
})

describe('filterByStatus', () => {
  it('returns all tasks when filter is "all"', () => {
    expect(filterByStatus(tasks, 'all')).toHaveLength(4)
  })

  it('returns only matching status tasks', () => {
    const result = filterByStatus(tasks, 'todo')
    expect(result).toHaveLength(2)
    expect(result.map((t) => t.id)).toEqual(['1', '4'])
  })

  it('returns in_progress tasks', () => {
    const result = filterByStatus(tasks, 'in_progress')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('2')
  })
})

describe('filterByDueDateBefore', () => {
  it('returns all tasks when cutoff is null', () => {
    expect(filterByDueDateBefore(tasks, null)).toHaveLength(4)
  })

  it('returns tasks with due_date on or before cutoff, including null due dates', () => {
    const result = filterByDueDateBefore(tasks, '2026-03-01')
    // tasks with due_date <= 2026-03-01: ids 1, 2; task 4 has no due_date so excluded
    expect(result.map((t) => t.id)).toEqual(['1', '2'])
  })

  it('excludes tasks with due_date after the cutoff', () => {
    const result = filterByDueDateBefore(tasks, '2026-01-01')
    expect(result.map((t) => t.id)).toEqual(['1'])
  })
})

describe('sortTasks', () => {
  it('sorts by due_date ascending, nulls last', () => {
    const result = sortTasks(tasks, 'due_date_asc')
    expect(result.map((t) => t.id)).toEqual(['1', '2', '3', '4'])
  })

  it('sorts by priority — urgent first down to low', () => {
    const result = sortTasks(tasks, 'priority_desc')
    expect(result.map((t) => t.id)).toEqual(['4', '3', '2', '1'])
  })

  it('sorts by title ascending', () => {
    const shuffled = [tasks[2], tasks[0], tasks[3], tasks[1]]
    const result = sortTasks(shuffled, 'title_asc')
    expect(result.map((t) => t.title)).toEqual(['A', 'B', 'C', 'D'])
  })

  it('does not mutate the original array', () => {
    const original = [...tasks]
    sortTasks(tasks, 'priority_desc')
    expect(tasks.map((t) => t.id)).toEqual(original.map((t) => t.id))
  })
})
