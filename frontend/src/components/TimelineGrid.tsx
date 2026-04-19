import React from 'react'
import { useDroppable } from '@dnd-kit/core'
import { formatHour, generateHourSlots, getBlockStyle, HOUR_HEIGHT } from '../utils/planner'
import ScheduleBlockItem from './ScheduleBlockItem'
import type { ScheduleBlock } from '../types/scheduleBlock'
import type { Task } from '../types/task'
import type { Project } from '../types/project'
import './TimelineGrid.css'

interface HourSlotProps {
  hour: number
}

function HourSlot({ hour }: HourSlotProps): React.JSX.Element {
  const { setNodeRef, isOver } = useDroppable({ id: `hour-slot-${hour}` })
  return (
    <div
      ref={setNodeRef}
      className={`timeline-hour-slot${isOver ? ' is-over' : ''}`}
      data-testid={`hour-slot-${hour}`}
      style={{ height: HOUR_HEIGHT }}
    />
  )
}

interface TimelineGridProps {
  workHoursStart: number
  workHoursEnd: number
  blocks: ScheduleBlock[]
  tasks: Map<string, Task>
  projects: Map<string, Project>
  onResizeBlock: (blockId: string, newEndHour: number) => void
  onDeleteBlock: (blockId: string) => void
}

function TimelineGrid({
  workHoursStart,
  workHoursEnd,
  blocks,
  tasks,
  projects,
  onDeleteBlock,
  onResizeBlock,
}: TimelineGridProps): React.JSX.Element {
  const slots = generateHourSlots(workHoursStart, workHoursEnd)
  const totalHeight = (workHoursEnd - workHoursStart) * HOUR_HEIGHT

  return (
    <div className="timeline-grid" data-testid="timeline-grid">
      {slots.map((hour) => (
        <div key={hour} className="timeline-hour-row" style={{ height: HOUR_HEIGHT }}>
          <div className="timeline-hour-label">{formatHour(hour)}</div>
          <HourSlot hour={hour} />
        </div>
      ))}
      <div className="timeline-blocks-overlay" style={{ height: totalHeight }}>
        {blocks.map((block) => {
          const task = tasks.get(block.task_id)
          const project = task ? projects.get(task.project_id) : undefined
          const blockStyle = getBlockStyle(block, workHoursStart, HOUR_HEIGHT)
          return (
            <ScheduleBlockItem
              key={block.id}
              block={block}
              task={task}
              projectColor={project?.color}
              style={blockStyle}
              workHoursEnd={workHoursEnd}
              onDelete={onDeleteBlock}
              onResizeBlock={onResizeBlock}
            />
          )
        })}
      </div>
    </div>
  )
}

export default TimelineGrid
