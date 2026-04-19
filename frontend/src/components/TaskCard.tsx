import React from 'react'
import './TaskCard.css'
import type { Task, TaskStatus } from '../types/task'
import TimerButton from './TimerButton'
import { useTimerStore } from '../stores/timerStore'
import { useActiveTimer, useStartTimer, useStopTimer } from '../api/timeEntries'

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'Todo',
  in_progress: 'In Progress',
  done: 'Done',
}

interface TaskCardProps {
  task: Task
  onClick?: () => void
}

function TaskCard({ task, onClick }: TaskCardProps): React.JSX.Element {
  const today = new Date(new Date().toDateString()) // midnight local time, no time component
  // Parse due_date as local midnight so comparison is timezone-consistent
  const isOverdue = task.due_date !== null && new Date(task.due_date + 'T00:00:00') < today

  const { data: activeEntry } = useActiveTimer()
  const startTimer = useStartTimer()
  const stopTimer = useStopTimer()
  const startTick = useTimerStore((s) => s.startTick)
  const stopTick = useTimerStore((s) => s.stopTick)

  const taskActiveEntry = activeEntry?.task_id === task.id ? activeEntry : null

  function handleStart() {
    startTimer.mutate(
      { task_id: task.id },
      {
        onSuccess: (entry) => {
          startTick(entry.id, entry.task_id)
        },
      },
    )
  }

  function handleStop(entryId: string) {
    stopTimer.mutate(entryId, {
      onSuccess: () => stopTick(),
    })
  }

  return (
    <div className="task-card" data-testid="task-card" onClick={onClick}>
      <span
        className={`task-priority-indicator priority-${task.priority}`}
        data-testid="task-priority-indicator"
      />
      <div className="task-card-body">
        <span className="task-card-title">{task.title}</span>
        {task.due_date && (
          <span
            className={`task-due-date${isOverdue ? ' overdue' : ''}`}
            data-testid="task-due-date"
          >
            {task.due_date}
          </span>
        )}
      </div>
      <div className="task-card-actions" data-testid="task-card-actions">
        <TimerButton
          activeEntry={taskActiveEntry}
          onStart={handleStart}
          onStop={handleStop}
        />
      </div>
      <span
        className={`task-status-badge status-${task.status}`}
        data-testid="task-status-badge"
      >
        {STATUS_LABELS[task.status]}
      </span>
    </div>
  )
}

export default TaskCard
