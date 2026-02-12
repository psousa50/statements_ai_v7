import { useState, useRef, useEffect, useCallback } from 'react'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import CheckIcon from '@mui/icons-material/Check'
import './StyledSelect.css'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

interface StyledSelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  disabled?: boolean
  id?: string
  placeholder?: string
}

export const StyledSelect = ({ value, onChange, options, disabled = false, id, placeholder }: StyledSelectProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const [focusedIndex, setFocusedIndex] = useState(-1)

  const selectedOption = options.find((o) => o.value === value)
  const displayLabel = selectedOption?.label ?? placeholder ?? ''

  const close = useCallback(() => {
    setIsOpen(false)
    setFocusedIndex(-1)
  }, [])

  useEffect(() => {
    if (!isOpen) return
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        close()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen, close])

  useEffect(() => {
    if (isOpen && listRef.current && focusedIndex >= 0) {
      const item = listRef.current.children[focusedIndex] as HTMLElement
      item?.scrollIntoView({ block: 'nearest' })
    }
  }, [focusedIndex, isOpen])

  const handleToggle = () => {
    if (disabled) return
    if (!isOpen) {
      const idx = options.findIndex((o) => o.value === value)
      setFocusedIndex(idx >= 0 ? idx : 0)
    }
    setIsOpen(!isOpen)
  }

  const handleSelect = (opt: SelectOption) => {
    if (opt.disabled) return
    onChange(opt.value)
    close()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return

    if (!isOpen) {
      if (['Enter', ' ', 'ArrowDown', 'ArrowUp'].includes(e.key)) {
        e.preventDefault()
        handleToggle()
      }
      return
    }

    switch (e.key) {
      case 'Escape':
        e.preventDefault()
        close()
        break
      case 'ArrowDown':
        e.preventDefault()
        setFocusedIndex((prev) => {
          let next = prev + 1
          while (next < options.length && options[next].disabled) next++
          return next < options.length ? next : prev
        })
        break
      case 'ArrowUp':
        e.preventDefault()
        setFocusedIndex((prev) => {
          let next = prev - 1
          while (next >= 0 && options[next].disabled) next--
          return next >= 0 ? next : prev
        })
        break
      case 'Enter':
      case ' ':
        e.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < options.length) {
          handleSelect(options[focusedIndex])
        }
        break
    }
  }

  return (
    <div ref={containerRef} className={`styled-select ${isOpen ? 'open' : ''} ${disabled ? 'disabled' : ''}`} id={id}>
      <button
        type="button"
        className="styled-select-trigger"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className={`styled-select-value ${!selectedOption && placeholder ? 'placeholder' : ''}`}>
          {displayLabel}
        </span>
        <KeyboardArrowDownIcon className={`styled-select-icon ${isOpen ? 'rotated' : ''}`} fontSize="small" />
      </button>

      {isOpen && (
        <ul ref={listRef} className="styled-select-dropdown" role="listbox">
          {options.map((opt, i) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={opt.value === value}
              className={`styled-select-option ${opt.value === value ? 'selected' : ''} ${opt.disabled ? 'disabled' : ''} ${i === focusedIndex ? 'focused' : ''}`}
              onClick={() => handleSelect(opt)}
              onMouseEnter={() => setFocusedIndex(i)}
            >
              <span className="styled-select-option-label">{opt.label}</span>
              {opt.value === value && <CheckIcon className="styled-select-check" fontSize="small" />}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
