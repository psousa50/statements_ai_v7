import { PRESET_COLORS } from '../utils/categoryColors'
import './ColorSwatchPicker.css'

interface ColorSwatchPickerProps {
  value: string | undefined
  onChange: (color: string) => void
  disabled?: boolean
}

export const ColorSwatchPicker = ({ value, onChange, disabled }: ColorSwatchPickerProps) => {
  return (
    <div className={`color-swatch-picker ${disabled ? 'disabled' : ''}`}>
      {PRESET_COLORS.map((color) => (
        <button
          key={color}
          type="button"
          className={`color-swatch ${value === color ? 'selected' : ''}`}
          style={{ backgroundColor: color }}
          onClick={() => !disabled && onChange(color)}
          disabled={disabled}
          aria-label={`Select colour ${color}`}
        >
          {value === color && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
        </button>
      ))}
    </div>
  )
}
