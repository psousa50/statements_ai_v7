import { useState, useEffect, useRef, useCallback } from 'react'
import { DateRangePicker } from 'rsuite'
import 'rsuite/dist/rsuite.min.css'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import {
  PeriodType,
  getPeriodRange,
  navigatePeriod,
  formatDateToString,
  parseDateString,
  detectPeriodType,
  formatCustomRangeLabel,
} from './dateUtils'
import './DatePeriodNavigator.css'

interface DatePeriodNavigatorProps {
  startDate?: string
  endDate?: string
  onChange: (startDate?: string, endDate?: string) => void
  defaultPeriodType?: PeriodType
}

const PERIOD_TYPES: PeriodType[] = ['all', 'week', 'month', 'year']

export function DatePeriodNavigator({
  startDate,
  endDate,
  onChange,
  defaultPeriodType = 'month',
}: DatePeriodNavigatorProps) {
  const [periodType, setPeriodType] = useState<PeriodType>(defaultPeriodType)
  const [currentPeriod, setCurrentPeriod] = useState<Date>(() => new Date())
  const [isCustomMode, setIsCustomMode] = useState(false)
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const customPickerRef = useRef<HTMLDivElement>(null)
  const hasInitialised = useRef(false)

  useEffect(() => {
    if (hasInitialised.current) return

    if (startDate && endDate) {
      const detected = detectPeriodType(startDate, endDate)
      if (detected) {
        setPeriodType(detected)
        setCurrentPeriod(parseDateString(startDate))
        setIsCustomMode(false)
      } else {
        setIsCustomMode(true)
        setCurrentPeriod(parseDateString(startDate))
      }
    } else {
      setPeriodType('all')
      setIsCustomMode(false)
    }

    hasInitialised.current = true
  }, [startDate, endDate])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (customPickerRef.current && !customPickerRef.current.contains(event.target as Node)) {
        setShowCustomPicker(false)
      }
    }

    if (showCustomPicker) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCustomPicker])

  const handlePeriodTypeChange = useCallback(
    (newType: PeriodType) => {
      setPeriodType(newType)
      setIsCustomMode(false)
      if (newType === 'all') {
        onChange(undefined, undefined)
      } else {
        const now = new Date()
        setCurrentPeriod(now)
        const range = getPeriodRange(newType, now)
        onChange(formatDateToString(range.startDate), formatDateToString(range.endDate))
      }
    },
    [onChange]
  )

  const handleNavigate = useCallback(
    (direction: 'prev' | 'next') => {
      const newDate = navigatePeriod(periodType, currentPeriod, direction)
      setCurrentPeriod(newDate)
      setIsCustomMode(false)
      const range = getPeriodRange(periodType, newDate)
      onChange(formatDateToString(range.startDate), formatDateToString(range.endDate))
    },
    [periodType, currentPeriod, onChange]
  )

  const handleCustomDateChange = useCallback(
    (range: [Date, Date] | null) => {
      if (range && range[0] && range[1]) {
        setIsCustomMode(true)
        setShowCustomPicker(false)
        setCurrentPeriod(range[0])
        onChange(formatDateToString(range[0]), formatDateToString(range[1]))
      }
    },
    [onChange]
  )

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'ArrowLeft') {
        event.preventDefault()
        handleNavigate('prev')
      } else if (event.key === 'ArrowRight') {
        event.preventDefault()
        handleNavigate('next')
      } else if (event.key === 'Escape' && showCustomPicker) {
        setShowCustomPicker(false)
      }
    },
    [handleNavigate, showCustomPicker]
  )

  const isAllDates = periodType === 'all'
  const displayLabel = isAllDates
    ? 'All dates'
    : isCustomMode
      ? formatCustomRangeLabel(startDate, endDate)
      : getPeriodRange(periodType, currentPeriod).displayLabel

  const dateRangeValue: [Date, Date] | null =
    startDate && endDate ? [parseDateString(startDate), parseDateString(endDate)] : null

  return (
    <div className="date-period-navigator" onKeyDown={handleKeyDown}>
      <div className="period-type-selector" role="group" aria-label="Period type">
        {PERIOD_TYPES.map((type) => (
          <button
            key={type}
            type="button"
            className={`period-type-btn ${periodType === type && !isCustomMode ? 'active' : ''}`}
            onClick={() => handlePeriodTypeChange(type)}
            aria-pressed={periodType === type && !isCustomMode}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
        <div className="custom-picker-container" ref={customPickerRef}>
          <button
            type="button"
            className={`period-type-btn custom-picker-trigger ${isCustomMode ? 'active' : ''}`}
            onClick={() => setShowCustomPicker(!showCustomPicker)}
            aria-expanded={showCustomPicker}
            aria-haspopup="dialog"
          >
            Custom
            <ExpandMoreIcon
              fontSize="small"
              className={`custom-picker-chevron ${showCustomPicker ? 'open' : ''}`}
            />
          </button>
          {showCustomPicker && (
            <div className="custom-picker-dropdown" role="dialog" aria-label="Custom date range">
              <DateRangePicker
                value={dateRangeValue}
                onChange={handleCustomDateChange}
                placeholder="Select date range"
                cleanable={false}
                showOneCalendar
                format="dd/MM/yyyy"
                character=" - "
                size="md"
                placement="bottomEnd"
                open
                oneTap={false}
              />
            </div>
          )}
        </div>
      </div>

      {!isAllDates && (
        <div className="period-navigation">
          <button
            type="button"
            className="nav-arrow"
            onClick={() => handleNavigate('prev')}
            aria-label={`Previous ${periodType}`}
          >
            <ChevronLeftIcon fontSize="small" />
          </button>

          <span className="period-label" aria-live="polite">
            {displayLabel}
          </span>

          <button
            type="button"
            className="nav-arrow"
            onClick={() => handleNavigate('next')}
            aria-label={`Next ${periodType}`}
          >
            <ChevronRightIcon fontSize="small" />
          </button>
        </div>
      )}

    </div>
  )
}
