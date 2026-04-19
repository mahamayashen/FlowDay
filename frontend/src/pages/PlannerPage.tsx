import React, { useState, useMemo, useRef, useEffect } from 'react'
import { DndContext, closestCenter } from '@dnd-kit/core'
import type { DragEndEvent } from '@dnd-kit/core'
import { useQueries } from '@tanstack/react-query'
import { usePlannerStore } from '../stores/plannerStore'
import { useProjects } from '../api/projects'
import { useScheduleBlocks, useCreateScheduleBlock, useUpdateScheduleBlock, useDeleteScheduleBlock } from '../api/scheduleBlocks'
import { fetchProjectTasks, TASK_KEYS } from '../api/tasks'
import DateNavigator from '../components/DateNavigator'
import TaskPool from '../components/TaskPool'
import TimelineGrid from '../components/TimelineGrid'
import type { Task } from '../types/task'
import type { Project } from '../types/project'
import './PlannerPage.css'

function PlannerPage(): React.JSX.Element {
  const { selectedDate, workHoursStart, workHoursEnd, setSelectedDate, goToNextDay, goToPrevDay } =
    usePlannerStore()

  const { data: projects = [] } = useProjects()
  const { data: blocks = [] } = useScheduleBlocks(selectedDate)

  const createBlock = useCreateScheduleBlock()
  const updateBlock = useUpdateScheduleBlock()
  const deleteBlock = useDeleteScheduleBlock()

  const [overlapError, setOverlapError] = useState<string | null>(null)
  const overlapTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (overlapTimerRef.current !== null) clearTimeout(overlapTimerRef.current)
    }
  }, [])

  const taskQueries = useQueries({
    queries: projects.map((p: Project) => ({
      queryKey: TASK_KEYS.byProject(p.id),
      queryFn: () => fetchProjectTasks(p.id),
      enabled: projects.length > 0,
    })),
  })

  const allTasks = useMemo<Task[]>(() => {
    return taskQueries.flatMap((q) => q.data ?? [])
  }, [taskQueries])

  const scheduledTaskIds = useMemo(
    () => new Set(blocks.map((b) => b.task_id)),
    [blocks],
  )

  const unscheduledTasks = useMemo(
    () => allTasks.filter((t) => !scheduledTaskIds.has(t.id)),
    [allTasks, scheduledTaskIds],
  )

  const tasksByProject = useMemo<Map<string, Task[]>>(() => {
    const map = new Map<string, Task[]>()
    for (const task of unscheduledTasks) {
      const list = map.get(task.project_id) ?? []
      list.push(task)
      map.set(task.project_id, list)
    }
    return map
  }, [unscheduledTasks])

  const taskMap = useMemo<Map<string, Task>>(() => {
    const map = new Map<string, Task>()
    for (const task of allTasks) {
      map.set(task.id, task)
    }
    return map
  }, [allTasks])

  const projectMap = useMemo<Map<string, Project>>(() => {
    const map = new Map<string, Project>()
    for (const project of projects) {
      map.set(project.id, project)
    }
    return map
  }, [projects])

  function showOverlapError(message: string): void {
    if (overlapTimerRef.current !== null) clearTimeout(overlapTimerRef.current)
    setOverlapError(message)
    overlapTimerRef.current = setTimeout(() => setOverlapError(null), 3000)
  }

  function handleDragEnd(event: DragEndEvent): void {
    const { active, over } = event
    if (!over) return

    const overId = String(over.id)
    if (!overId.startsWith('hour-slot-')) return

    const dropHour = parseInt(overId.replace('hour-slot-', ''), 10)
    const activeData = active.data.current

    if (activeData?.type === 'task') {
      const task = activeData.task as Task
      const durationHours = task.estimate_minutes ? task.estimate_minutes / 60 : 1
      const endHour = Math.min(dropHour + durationHours, workHoursEnd)

      createBlock.mutate(
        { data: { task_id: task.id, date: selectedDate, start_hour: dropHour, end_hour: endHour, source: 'manual' } },
        {
          onError: () => showOverlapError('This time slot overlaps with an existing block.'),
        },
      )
    } else if (activeData?.type === 'block') {
      const block = activeData.block
      const duration = block.end_hour - block.start_hour
      const newEndHour = Math.min(dropHour + duration, workHoursEnd)

      updateBlock.mutate(
        { blockId: block.id, originalDate: block.date, data: { date: selectedDate, start_hour: dropHour, end_hour: newEndHour } },
        {
          onError: () => showOverlapError('This time slot overlaps with an existing block.'),
        },
      )
    }
  }

  function handleResizeBlock(blockId: string, newEndHour: number): void {
    const block = blocks.find((b) => b.id === blockId)
    if (!block) return
    updateBlock.mutate(
      { blockId, originalDate: block.date, data: { date: block.date, start_hour: block.start_hour, end_hour: newEndHour } },
      { onError: () => showOverlapError('Cannot resize: overlaps with an existing block.') },
    )
  }

  function handleDeleteBlock(blockId: string): void {
    const block = blocks.find((b) => b.id === blockId)
    if (!block) return
    deleteBlock.mutate({ blockId, date: block.date })
  }

  return (
    <main className="planner-page" data-testid="page-planner">
      <DateNavigator
        selectedDate={selectedDate}
        onPrevDay={goToPrevDay}
        onNextDay={goToNextDay}
        onDateChange={setSelectedDate}
      />
      {overlapError && (
        <div className="planner-overlap-error" role="alert">
          {overlapError}
        </div>
      )}
      <div className="planner-layout">
        <TaskPool projects={projects} tasksByProject={tasksByProject} />
        <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <TimelineGrid
            workHoursStart={workHoursStart}
            workHoursEnd={workHoursEnd}
            blocks={blocks}
            tasks={taskMap}
            projects={projectMap}
            onResizeBlock={handleResizeBlock}
            onDeleteBlock={handleDeleteBlock}
          />
        </DndContext>
      </div>
    </main>
  )
}

export default PlannerPage
