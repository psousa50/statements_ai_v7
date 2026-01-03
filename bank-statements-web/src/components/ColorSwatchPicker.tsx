import { PRESET_COLORS } from '../utils/categoryColors'
import './ColorSwatchPicker.css'

interface ColorSwatchPickerProps {
  value: string | undefined
  onChange: (color: string) => void
  disabled?: boolean
  usedColors?: Map<string, string[]>
}

export const ColorSwatchPicker = ({ value, onChange, disabled, usedColors }: ColorSwatchPickerProps) => {
  return (
    <div className={`color-swatch-picker ${disabled ? 'disabled' : ''}`}>
      {PRESET_COLORS.map((color) => {
        const usedBy = usedColors?.get(color) || []
        const isUsed = usedBy.length > 0
        const isSelected = value === color

        return (
          <div key={color} className="color-swatch-container">
            <button
              type="button"
              className={`color-swatch ${isSelected ? 'selected' : ''} ${isUsed && !isSelected ? 'used' : ''}`}
              style={{ backgroundColor: color }}
              onClick={() => !disabled && onChange(color)}
              disabled={disabled}
              aria-label={`Select colour ${color}${isUsed ? ` (used by ${usedBy.join(', ')})` : ''}`}
              title={isUsed ? `Used by: ${usedBy.join(', ')}` : 'Available'}
            >
              {isSelected && (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
              {isUsed && !isSelected && <span className="used-count">{usedBy.length}</span>}
            </button>
          </div>
        )
      })}
    </div>
  )
}
