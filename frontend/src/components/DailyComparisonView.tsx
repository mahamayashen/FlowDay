import React from 'react'
import type { TaskComparison } from '../types/analytics'
import { statusTagColor } from '../utils/reviewUtils'

interface DailyComparisonViewProps {
  tasks: TaskComparison[]
}

function DailyComparisonView({ tasks }: DailyComparisonViewProps): React.JSX.Element {
  if (tasks.length === 0) {
    return <p>No tasks scheduled</p>
  }

  return (
    <ul>
      {tasks.map((task) => (
        <li key={task.task_id}>
          <span>{task.task_title}</span>
          <span data-testid={`planned-${task.task_id}`}>{task.planned_hours.toFixed(2)}h</span>
          <span data-testid={`actual-${task.task_id}`}>{task.actual_hours.toFixed(2)}h</span>
          <span
            data-testid={`status-badge-${task.task_id}`}
            style={{ backgroundColor: statusTagColor(task.status) }}
          >
            {task.status}
          </span>
        </li>
      ))}
    </ul>
  )
}

export default DailyComparisonView
