import React, { useState, useRef, useEffect } from 'react'
import { useDraggable } from '@dnd-kit/core'
import { HOUR_HEIGHT } from '../utils/planner'
import type { ScheduleBlock } from '../types/scheduleBlock'
import type { Task } from '../types/task'
import './ScheduleBlockItem.css'

interface ScheduleBlockItemProps {
  block: ScheduleBlock
  task: Task | undefined
  projectColor: string | undefined
  style: { top: number; height: number }
  workHoursEnd: number
  onDelete: (blockId: string) => void
  onResizeBlock: (blockId: string, newEndHour: number) => void
}

function ScheduleBlockItem({
  block,
  task,
  projectColor,
  style,
  workHoursEnd,
  onDelete,
  onResizeBlock,
}: ScheduleBlockItemProps): React.JSX.Element {
  const isCalendar = block.source === 'google_calendar'
  const [resizeHeight, setResizeHeight] = useState<number | null>(null)
  const startYRef = useRef<number>(0)
  const startHeightRef = useRef<number>(0)
  const deleteBtnRef = useRef<HTMLButtonElement | null>(null)

  // Stop pointerdown on the delete button at the NATIVE capture phase so
  // dnd-kit's activation never sees it. React-level stopPropagation on the
  // React onPointerDown handler isn't enough: dnd-kit ships its own sensor
  // pipeline and the React synthetic event isn't guaranteed to short-circuit
  // it in every build. Ref-mounted capture listener is belt-and-suspenders.
  useEffect(() => {
    const btn = deleteBtnRef.current
    if (!btn) return
    const stop = (e: Event): void => {
      e.stopPropagation()
      e.stopImmediatePropagation()
    }
    btn.addEventListener('pointerdown', stop, true)
    return () => {
      btn.removeEventListener('pointerdown', stop, true)
    }
  }, [])

  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: block.id,
    disabled: isCalendar,
    data: { type: 'block', block },
  })

  function handleResizePointerDown(e: React.PointerEvent<HTMLDivElement>): void {
    e.stopPropagation()
    e.currentTarget.setPointerCapture?.(e.pointerId)
    startYRef.current = e.clientY
    startHeightRef.current = style.height
    setResizeHeight(style.height)
  }

  function handleResizePointerMove(e: React.PointerEvent<HTMLDivElement>): void {
    if (resizeHeight === null) return
    const delta = e.clientY - startYRef.current
    const newHeight = Math.max(HOUR_HEIGHT * 0.25, startHeightRef.current + delta)
    setResizeHeight(newHeight)
  }

  function handleResizePointerUp(): void {
    if (resizeHeight === null) return
    const rawEndHour = block.start_hour + resizeHeight / HOUR_HEIGHT
    const snapped = Math.round(rawEndHour * 4) / 4
    const clamped = Math.min(Math.max(snapped, block.start_hour + 0.25), workHoursEnd)
    onResizeBlock(block.id, clamped)
    setResizeHeight(null)
  }

  const displayHeight = resizeHeight ?? style.height

  const blockStyle: React.CSSProperties = {
    top: style.top,
    height: displayHeight,
    borderLeftColor: isCalendar ? '#3b82f6' : (projectColor ?? '#6b7280'),
    opacity: isDragging ? 0.4 : 1,
  }

  const testId = isCalendar ? 'calendar-block' : 'schedule-block'

  return (
    <div
      ref={isCalendar ? undefined : setNodeRef}
      className={`schedule-block-item${isCalendar ? ' calendar' : ''}`}
      style={blockStyle}
      data-testid={testId}
      data-block-id={block.id}
      {...(isCalendar ? {} : { ...listeners, ...attributes })}
    >
      <div className="schedule-block-title">
        {task?.title ?? (isCalendar ? 'Calendar event' : 'Unknown task')}
      </div>
      {!isCalendar && (
        <>
          <button
            ref={deleteBtnRef}
            className="schedule-block-delete"
            data-testid="delete-block-btn"
            onPointerDown={(e) => {
              // React-level stopPropagation (paired with the capture-phase
              // listener in useEffect above) keeps dnd-kit from claiming this
              // pointerdown as a drag-start.
              e.stopPropagation()
            }}
            onClick={(e) => {
              e.stopPropagation()
              onDelete(block.id)
            }}
            aria-label="Delete block"
          >
            ×
          </button>
          <div
            className="resize-handle"
            data-testid="resize-handle"
            onPointerDown={handleResizePointerDown}
            onPointerMove={handleResizePointerMove}
            onPointerUp={() => handleResizePointerUp()}
            onPointerCancel={() => setResizeHeight(null)}
          />
        </>
      )}
    </div>
  )
}

export default ScheduleBlockItem
