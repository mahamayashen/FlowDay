import React from 'react'
import Modal from './Modal'
import './ConfirmDialog.css'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: React.ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** If true, the confirm button uses the danger style. Default: true. */
  destructive?: boolean
  onConfirm: () => void
  onCancel: () => void
  isPending?: boolean
}

function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Delete',
  cancelLabel = 'Cancel',
  destructive = true,
  onConfirm,
  onCancel,
  isPending = false,
}: ConfirmDialogProps): React.JSX.Element {
  return (
    <Modal open={open} onClose={onCancel} title={title} size="sm">
      <div className="confirm-dialog">
        <p className="confirm-dialog-message">{message}</p>
        <div className="confirm-dialog-actions">
          <button
            type="button"
            className="confirm-dialog-cancel"
            onClick={onCancel}
            disabled={isPending}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`confirm-dialog-confirm${destructive ? ' confirm-dialog-confirm--danger' : ''}`}
            onClick={onConfirm}
            disabled={isPending}
            data-testid="confirm-dialog-confirm"
          >
            {isPending ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default ConfirmDialog
