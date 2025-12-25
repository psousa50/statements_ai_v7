export type PeriodType = 'week' | 'month' | 'year'

export interface PeriodRange {
  startDate: Date
  endDate: Date
  displayLabel: string
}

export function formatDateToString(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function parseDateString(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function getMonday(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  d.setDate(diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function getSunday(date: Date): Date {
  const monday = getMonday(date)
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  sunday.setHours(23, 59, 59, 999)
  return sunday
}

function formatShortMonth(date: Date): string {
  return date.toLocaleDateString('en-GB', { month: 'short' })
}

function formatFullMonth(date: Date): string {
  return date.toLocaleDateString('en-GB', { month: 'long' })
}

export function getWeekRange(date: Date): PeriodRange {
  const startDate = getMonday(date)
  const endDate = getSunday(date)

  const startDay = startDate.getDate()
  const endDay = endDate.getDate()
  const startMonth = formatShortMonth(startDate)
  const endMonth = formatShortMonth(endDate)
  const year = endDate.getFullYear()

  let displayLabel: string
  if (startDate.getMonth() === endDate.getMonth()) {
    displayLabel = `${startDay}-${endDay} ${startMonth} ${year}`
  } else if (startDate.getFullYear() === endDate.getFullYear()) {
    displayLabel = `${startDay} ${startMonth} - ${endDay} ${endMonth} ${year}`
  } else {
    displayLabel = `${startDay} ${startMonth} ${startDate.getFullYear()} - ${endDay} ${endMonth} ${year}`
  }

  return { startDate, endDate, displayLabel }
}

export function getMonthRange(date: Date): PeriodRange {
  const startDate = new Date(date.getFullYear(), date.getMonth(), 1)
  startDate.setHours(0, 0, 0, 0)

  const endDate = new Date(date.getFullYear(), date.getMonth() + 1, 0)
  endDate.setHours(23, 59, 59, 999)

  const displayLabel = `${formatFullMonth(date)} ${date.getFullYear()}`

  return { startDate, endDate, displayLabel }
}

export function getYearRange(date: Date): PeriodRange {
  const year = date.getFullYear()

  const startDate = new Date(year, 0, 1)
  startDate.setHours(0, 0, 0, 0)

  const endDate = new Date(year, 11, 31)
  endDate.setHours(23, 59, 59, 999)

  const displayLabel = String(year)

  return { startDate, endDate, displayLabel }
}

export function getPeriodRange(periodType: PeriodType, date: Date): PeriodRange {
  switch (periodType) {
    case 'week':
      return getWeekRange(date)
    case 'month':
      return getMonthRange(date)
    case 'year':
      return getYearRange(date)
  }
}

export function navigatePeriod(
  periodType: PeriodType,
  currentDate: Date,
  direction: 'prev' | 'next'
): Date {
  const result = new Date(currentDate)
  const delta = direction === 'next' ? 1 : -1

  switch (periodType) {
    case 'week':
      result.setDate(result.getDate() + delta * 7)
      break
    case 'month':
      result.setMonth(result.getMonth() + delta)
      break
    case 'year':
      result.setFullYear(result.getFullYear() + delta)
      break
  }

  return result
}

export function getPeriodDisplayLabel(periodType: PeriodType, date: Date): string {
  return getPeriodRange(periodType, date).displayLabel
}

function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  )
}

export function detectPeriodType(startDateStr: string, endDateStr: string): PeriodType | null {
  const startDate = parseDateString(startDateStr)
  const endDate = parseDateString(endDateStr)

  const weekRange = getWeekRange(startDate)
  if (isSameDay(weekRange.startDate, startDate) && isSameDay(weekRange.endDate, endDate)) {
    return 'week'
  }

  const monthRange = getMonthRange(startDate)
  if (isSameDay(monthRange.startDate, startDate) && isSameDay(monthRange.endDate, endDate)) {
    return 'month'
  }

  const yearRange = getYearRange(startDate)
  if (isSameDay(yearRange.startDate, startDate) && isSameDay(yearRange.endDate, endDate)) {
    return 'year'
  }

  return null
}

export function formatCustomRangeLabel(startDateStr?: string, endDateStr?: string): string {
  if (!startDateStr || !endDateStr) {
    return 'Select dates'
  }

  const startDate = parseDateString(startDateStr)
  const endDate = parseDateString(endDateStr)

  const startDay = startDate.getDate()
  const endDay = endDate.getDate()
  const startMonth = formatShortMonth(startDate)
  const endMonth = formatShortMonth(endDate)
  const startYear = startDate.getFullYear()
  const endYear = endDate.getFullYear()

  if (startYear === endYear && startDate.getMonth() === endDate.getMonth()) {
    return `${startDay}-${endDay} ${startMonth} ${startYear}`
  } else if (startYear === endYear) {
    return `${startDay} ${startMonth} - ${endDay} ${endMonth} ${startYear}`
  } else {
    return `${startDay} ${startMonth} ${startYear} - ${endDay} ${endMonth} ${endYear}`
  }
}
