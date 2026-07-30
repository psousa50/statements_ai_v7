import { useState, useEffect } from 'react'
import { Tag } from '../types/Transaction'

interface TagModalProps {
  isOpen: boolean
  tag: Tag | null
  onSave: (name: string, tagId?: string) => Promise<void>
  onClose: () => void
}

export const TagModal = ({ isOpen, tag, onSave, onClose }: TagModalProps) => {
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)

  const isEditing = !!tag
  const title = isEditing ? 'Rename Tag' : 'Create Tag'

  useEffect(() => {
    if (isOpen) {
      setName(tag ? tag.name : '')
    }
  }, [isOpen, tag])

  if (!isOpen) return null

  const handleSave = async () => {
    const trimmedName = name.trim()
    if (!trimmedName) return

    setSaving(true)
    try {
      await onSave(trimmedName, tag?.id)
    } finally {
      setSaving(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !saving && name.trim()) {
      handleSave()
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="tag-name" className="form-label">
              Tag Name *
            </label>
            <input
              id="tag-name"
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Enter tag name"
              maxLength={50}
              disabled={saving}
              autoFocus
            />
          </div>
        </div>

        <div className="modal-footer">
          <button className="button-secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button className="button-primary" onClick={handleSave} disabled={saving || !name.trim()}>
            {saving ? 'Saving...' : isEditing ? 'Rename Tag' : 'Create Tag'}
          </button>
        </div>
      </div>
    </div>
  )
}
