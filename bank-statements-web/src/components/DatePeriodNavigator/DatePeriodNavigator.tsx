import { useState, useEffect, useRef, useCallback } from 'react'
import { DayPicker, DateRange } from 'react-day-picker'
import 'react-day-picker/style.css'
import {
  startOfDay,
  endOfDay,
  subDays,
  subMonths,
  addMonths,
  addDays,
  startOfWeek,
  endOfWeek,
  subWeeks,
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
  detectRollingWindow,
  formatCustomRangeLabel,
  RollingWindow,
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

const PERIOD_TYPES: PeriodType[] = ['day', 'week', 'month', 'year', 'all']

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
      const firstDay = new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1)
      const lastDay = new Date(lastMonth.getFullYear(), lastMonth.getMonth() + 1, 0)
      return { from: startOfDay(firstDay), to: endOfDay(lastDay) }
    },
  },
  {
    label: 'Last 3 months',
    getRange: () => ({ from: startOfDay(subMonths(new Date(), 3)), to: endOfDay(new Date()) }),
  },
  {
    label: 'Last 6 months',
    getRange: () => ({ from: startOfDay(subMonths(new Date(), 6)), to: endOfDay(new Date()) }),
  },
  {
    label: 'Last 9 months',
    getRange: () => ({ from: startOfDay(subMonths(new Date(), 9)), to: endOfDay(new Date()) }),
  },
]

export function DatePeriodNavigator({
  startDate,
  endDate,
  onChange,
  defaultPeriodType = 'month',
}: DatePeriodNavigatorProps) {
  const [periodType, setPeriodType] = useState<PeriodType>(() => {
    if (startDate && endDate) {
      return detectPeriodType(startDate, endDate) || defaultPeriodType
    }
    return defaultPeriodType
  })
  const [currentPeriod, setCurrentPeriod] = useState<Date>(() => {
    if (startDate) {
      return parseDateString(startDate)
    }
    return new Date()
  })
  const [isCustomMode, setIsCustomMode] = useState(() => {
    if (startDate && endDate) {
      return detectPeriodType(startDate, endDate) === null
    }
    return false
  })
  const [rollingWindow, setRollingWindow] = useState<RollingWindow | null>(() => {
    if (startDate && endDate && detectPeriodType(startDate, endDate) === null) {
      return detectRollingWindow(startDate, endDate)
    }
    return null
  })
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const [selectedRange, setSelectedRange] = useState<DateRange | undefined>(() => {
    if (startDate && endDate) {
      return { from: parseDateString(startDate), to: parseDateString(endDate) }
    }
    return undefined
  })
  const firstSelectedDateRef = useRef<Date | null>(null)
  const customPickerRef = useRef<HTMLDivElement>(null)
  const hasInitialised = useRef(false)

  useEffect(() => {
    if (hasInitialised.current) return
    hasInitialised.current = true

    if (!startDate && !endDate && defaultPeriodType !== 'all') {
      const now = new Date()
      const range = getPeriodRange(defaultPeriodType, now)
      onChange(formatDateToString(range.startDate), formatDateToString(range.endDate))
      setSelectedRange({ from: range.startDate, to: range.endDate })
    }
  }, [])

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
      setRollingWindow(null)
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
      if (rollingWindow) {
        const delta = direction === 'next' ? 1 : -1
        const currentFrom = selectedRange?.from || new Date()
        const currentTo = selectedRange?.to || new Date()
        let newFrom: Date
        let newTo: Date
        if (rollingWindow.unit === 'months') {
          newFrom = startOfDay(addMonths(currentFrom, delta * rollingWindow.amount))
          newTo = endOfDay(addMonths(currentTo, delta * rollingWindow.amount))
        } else {
          newFrom = startOfDay(addDays(currentFrom, delta * rollingWindow.amount))
          newTo = endOfDay(addDays(currentTo, delta * rollingWindow.amount))
        }
        setSelectedRange({ from: newFrom, to: newTo })
        setCurrentPeriod(newFrom)
        onChange(formatDateToString(newFrom), formatDateToString(newTo))
        return
      }

      const newDate = navigatePeriod(periodType, currentPeriod, direction)
      setCurrentPeriod(newDate)
      setIsCustomMode(false)
      const range = getPeriodRange(periodType, newDate)
      onChange(formatDateToString(range.startDate), formatDateToString(range.endDate))
      setSelectedRange({ from: range.startDate, to: range.endDate })
    },
    [periodType, currentPeriod, onChange, rollingWindow, selectedRange]
  )

  const completeRangeSelection = useCallback(
    (from: Date, to: Date) => {
      const startStr = formatDateToString(from)
      const endStr = formatDateToString(to)
      const detected = detectPeriodType(startStr, endStr)

      if (detected) {
        setPeriodType(detected)
        setIsCustomMode(false)
        setRollingWindow(null)
      } else {
        setIsCustomMode(true)
        setRollingWindow(detectRollingWindow(startStr, endStr))
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
          className={`nav-arrow ${isCustomMode && !rollingWindow ? 'hidden' : ''}`}
          onClick={() => handleNavigate('prev')}
          aria-label={rollingWindow ? 'Previous period' : `Previous ${periodType}`}
        >
          <ChevronLeftIcon fontSize="small" />
        </button>

        <button type="button" className="period-label" onClick={handleToggleCustomPicker} aria-live="polite">
          {displayLabel}
        </button>

        <button
          type="button"
          className={`nav-arrow ${isCustomMode && !rollingWindow ? 'hidden' : ''}`}
          onClick={() => handleNavigate('next')}
          aria-label={rollingWindow ? 'Next period' : `Next ${periodType}`}
        >
          <ChevronRightIcon fontSize="small" />
        </button>
      </div>
    </div>
  )
}
