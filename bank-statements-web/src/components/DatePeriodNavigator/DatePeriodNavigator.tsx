import { useState, useEffect, useRef, useCallback } from 'react'
import { DayPicker, DateRange } from 'react-day-picker'
import 'react-day-picker/style.css'
import {
  startOfDay,
  endOfDay,
  subDays,
  startOfMonth,
  endOfMonth,
  subMonths,
  startOfWeek,
  endOfWeek,
  subWeeks,
  startOfYear,
  endOfYear,
  subYears,
} from 'date-fns'
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

interface PresetRange {
  label: string
  getRange: () => { from: Date; to: Date }
}

const PERIOD_TYPES: PeriodType[] = ['week', 'month', 'year', 'all']

const PRESET_RANGES: PresetRange[] = [
  {
    label: 'Today',
    getRange: () => ({ from: startOfDay(new Date()), to: endOfDay(new Date()) }),
  },
  {
    label: 'Yesterday',
    getRange: () => {
      const yesterday = subDays(new Date(), 1)
      return { from: startOfDay(yesterday), to: endOfDay(yesterday) }
    },
  },
  {
    label: 'Last 7 days',
    getRange: () => ({ from: startOfDay(subDays(new Date(), 6)), to: endOfDay(new Date()) }),
  },
  {
    label: 'Last 30 days',
    getRange: () => ({ from: startOfDay(subDays(new Date(), 29)), to: endOfDay(new Date()) }),
  },
  {
    label: 'Last week',
    getRange: () => {
      const lastWeek = subWeeks(new Date(), 1)
      return {
        from: startOfWeek(lastWeek, { weekStartsOn: 1 }),
        to: endOfWeek(lastWeek, { weekStartsOn: 1 }),
      }
    },
  },
  {
    label: 'Last month',
    getRange: () => {
      const lastMonth = subMonths(new Date(), 1)
      return { from: startOfMonth(lastMonth), to: endOfMonth(lastMonth) }
    },
  },
  {
    label: 'Last year',
    getRange: () => {
      const lastYear = subYears(new Date(), 1)
      return { from: startOfYear(lastYear), to: endOfYear(lastYear) }
    },
  },
]

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
  const [selectedRange, setSelectedRange] = useState<DateRange | undefined>(undefined)
  const firstSelectedDateRef = useRef<Date | null>(null)
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
      setSelectedRange({
        from: parseDateString(startDate),
        to: parseDateString(endDate),
      })
    } else {
      setPeriodType(defaultPeriodType)
      setIsCustomMode(false)
      if (defaultPeriodType !== 'all') {
        const now = new Date()
        const range = getPeriodRange(defaultPeriodType, now)
        onChange(formatDateToString(range.startDate), formatDateToString(range.endDate))
        setSelectedRange({ from: range.startDate, to: range.endDate })
      }
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
        setSelectedRange(undefined)
      } else {
        const now = new Date()
        setCurrentPeriod(now)
        const range = getPeriodRange(newType, now)
        onChange(formatDateToString(range.startDate), formatDateToString(range.endDate))
        setSelectedRange({ from: range.startDate, to: range.endDate })
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
      setSelectedRange({ from: range.startDate, to: range.endDate })
    },
    [periodType, currentPeriod, onChange]
  )

  const completeRangeSelection = useCallback(
    (from: Date, to: Date) => {
      const startStr = formatDateToString(from)
      const endStr = formatDateToString(to)
      const detected = detectPeriodType(startStr, endStr)

      if (detected) {
        setPeriodType(detected)
        setIsCustomMode(false)
      } else {
        setIsCustomMode(true)
      }

      setShowCustomPicker(false)
      setCurrentPeriod(from)
      firstSelectedDateRef.current = null
      onChange(startStr, endStr)
    },
    [onChange]
  )

  const handleRangeSelect = useCallback(
    (range: DateRange | undefined) => {
      setSelectedRange(range)

      if (!range?.from && firstSelectedDateRef.current) {
        const date = firstSelectedDateRef.current
        completeRangeSelection(date, date)
        return
      }

      if (range?.from) {
        if (range.to && range.from.getTime() !== range.to.getTime()) {
          completeRangeSelection(range.from, range.to)
          return
        }

        firstSelectedDateRef.current = range.from
      }
    },
    [completeRangeSelection]
  )

  const handlePresetClick = useCallback(
    (preset: PresetRange) => {
      const { from, to } = preset.getRange()
      setSelectedRange({ from, to })
      completeRangeSelection(from, to)
    },
    [completeRangeSelection]
  )

  const handleToggleCustomPicker = useCallback(() => {
    if (!showCustomPicker) {
      setSelectedRange(undefined)
      firstSelectedDateRef.current = null
    }
    setShowCustomPicker(!showCustomPicker)
  }, [showCustomPicker])

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
  const displayLabel = isCustomMode
    ? formatCustomRangeLabel(startDate, endDate)
    : isAllDates
      ? 'All dates'
      : getPeriodRange(periodType, currentPeriod).displayLabel

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
            onClick={handleToggleCustomPicker}
            aria-expanded={showCustomPicker}
            aria-haspopup="dialog"
          >
            Custom
            <ExpandMoreIcon fontSize="small" className={`custom-picker-chevron ${showCustomPicker ? 'open' : ''}`} />
          </button>
          {showCustomPicker && (
            <div className="custom-picker-dropdown" role="dialog" aria-label="Custom date range">
              <div className="date-picker-layout">
                <div className="preset-panel">
                  {PRESET_RANGES.map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      className="preset-btn"
                      onClick={() => handlePresetClick(preset)}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
                <div className="calendar-panel">
                  <DayPicker
                    mode="range"
                    selected={selectedRange}
                    onSelect={handleRangeSelect}
                    numberOfMonths={1}
                    showOutsideDays
                    weekStartsOn={1}
                    defaultMonth={selectedRange?.from || new Date()}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className={`period-navigation ${isAllDates && !isCustomMode ? 'hidden' : ''}`}>
        <button
          type="button"
          className={`nav-arrow ${isCustomMode ? 'hidden' : ''}`}
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
          className={`nav-arrow ${isCustomMode ? 'hidden' : ''}`}
          onClick={() => handleNavigate('next')}
          aria-label={`Next ${periodType}`}
        >
          <ChevronRightIcon fontSize="small" />
        </button>
      </div>
    </div>
  )
}
