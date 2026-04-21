import React, { useState } from 'react'
import { PencilSimple, Trash } from '@phosphor-icons/react'
import './TaskCard.css'
import type { Task, TaskStatus } from '../types/task'
import TimerButton from './TimerButton'
import ConfirmDialog from './ConfirmDialog'
import { useTimerStore } from '../stores/timerStore'
import { useActiveTimer, useStartTimer, useStopTimer } from '../api/timeEntries'
import { useDeleteTask } from '../api/tasks'

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'Todo',
  in_progress: 'In Progress',
  done: 'Done',
}

interface TaskCardProps {
  task: Task
  onClick?: () => void
  /** When provided, edit/delete affordances render. */
  projectId?: string
  onEdit?: () => void
}

function TaskCard({ task, onClick, projectId, onEdit }: TaskCardProps): React.JSX.Element {
  const today = new Date(new Date().toDateString()) // midnight local time, no time component
  // Parse due_date as local midnight so comparison is timezone-consistent
  const isOverdue = task.due_date !== null && new Date(task.due_date + 'T00:00:00') < today

  const { data: activeEntry } = useActiveTimer()
  const startTimer = useStartTimer()
  const stopTimer = useStopTimer()
  const startTick = useTimerStore((s) => s.startTick)
  const stopTick = useTimerStore((s) => s.stopTick)
  const deleteTask = useDeleteTask()

  const [confirmingDelete, setConfirmingDelete] = useState(false)

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

  function handleConfirmDelete() {
    if (!projectId) return
    deleteTask.mutate(
      { projectId, taskId: task.id },
      { onSuccess: () => setConfirmingDelete(false) },
    )
  }

  const canManage = Boolean(projectId)

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
        {canManage && onEdit && (
          <button
            type="button"
            className="task-action-btn"
            aria-label={`Edit task ${task.title}`}
            onClick={(e) => {
              e.stopPropagation()
              onEdit()
            }}
            data-testid="btn-edit-task"
          >
            <PencilSimple size={13} weight="bold" />
          </button>
        )}
        {canManage && (
          <button
            type="button"
            className="task-action-btn task-action-btn--danger"
            aria-label={`Delete task ${task.title}`}
            onClick={(e) => {
              e.stopPropagation()
              setConfirmingDelete(true)
            }}
            data-testid="btn-delete-task"
          >
            <Trash size={13} weight="bold" />
          </button>
        )}
      </div>
      <span
        className={`task-status-badge status-${task.status}`}
        data-testid="task-status-badge"
      >
        {STATUS_LABELS[task.status]}
      </span>

      {canManage && (
        <ConfirmDialog
          open={confirmingDelete}
          title="Delete task?"
          message={
            <>
              Permanently delete <strong>{task.title}</strong>? This cannot be undone.
            </>
          }
          confirmLabel="Delete task"
          onConfirm={handleConfirmDelete}
          onCancel={() => setConfirmingDelete(false)}
          isPending={deleteTask.isPending}
        />
      )}
    </div>
  )
}

export default TaskCard
