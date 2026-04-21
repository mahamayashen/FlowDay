import React, { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from '@phosphor-icons/react'
import './Modal.css'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  /** optional width preset: 'sm' = 380px, 'md' = 480px (default), 'lg' = 640px */
  size?: 'sm' | 'md' | 'lg'
}

function Modal({ open, onClose, title, children, size = 'md' }: ModalProps): React.JSX.Element | null {
  const backdropRef = useRef<HTMLDivElement>(null)

  // Close on Esc key
  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent): void {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onClose])

  // Lock body scroll while open
  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [open])

  if (!open) return null

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>): void {
    if (e.target === backdropRef.current) onClose()
  }

  return createPortal(
    <div
      ref={backdropRef}
      className="modal-backdrop"
      onClick={handleBackdropClick}
      data-testid="modal-backdrop"
    >
      <div
        className={`modal-panel modal-panel--${size}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        data-testid="modal-panel"
      >
        <header className="modal-head">
          <h2 className="modal-title">{title}</h2>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close"
            data-testid="modal-close"
          >
            <X size={16} weight="bold" />
          </button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>,
    document.body,
  )
}

export default Modal
