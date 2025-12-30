export type PeriodType = 'all' | 'week' | 'month' | 'year'

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
    case 'all':
      return { startDate: date, endDate: date, displayLabel: 'All dates' }
    case 'week':
      return getWeekRange(date)
    case 'month':
      return getMonthRange(date)
    case 'year':
      return getYearRange(date)
  }
}

export function navigatePeriod(periodType: PeriodType, currentDate: Date, direction: 'prev' | 'next'): Date {
  const result = new Date(currentDate)
  const delta = direction === 'next' ? 1 : -1

  switch (periodType) {
    case 'all':
      break
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

export interface RollingWindow {
  amount: number
  unit: 'days' | 'months'
}

function getDaysDifference(start: Date, end: Date): number {
  const msPerDay = 24 * 60 * 60 * 1000
  return Math.round((end.getTime() - start.getTime()) / msPerDay) + 1
}

function getCalendarMonthsSpan(start: Date, end: Date): number | null {
  if (start.getDate() !== 1) return null

  const lastDayOfEndMonth = new Date(end.getFullYear(), end.getMonth() + 1, 0).getDate()
  if (end.getDate() !== lastDayOfEndMonth) return null

  const months =
    (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1

  return months > 0 ? months : null
}

function getRollingMonthsDifference(start: Date, end: Date): number | null {
  const startNormalised = new Date(start.getFullYear(), start.getMonth(), start.getDate())
  const endNormalised = new Date(end.getFullYear(), end.getMonth(), end.getDate())

  const monthsDiff =
    (endNormalised.getFullYear() - startNormalised.getFullYear()) * 12 +
    (endNormalised.getMonth() - startNormalised.getMonth())

  if (monthsDiff <= 0) return null

  const expectedEnd = new Date(startNormalised)
  expectedEnd.setMonth(expectedEnd.getMonth() + monthsDiff)

  const daysDiff = Math.abs(endNormalised.getTime() - expectedEnd.getTime()) / (24 * 60 * 60 * 1000)
  if (daysDiff <= 3) {
    return monthsDiff
  }

  return null
}

export function detectRollingWindow(startDateStr: string, endDateStr: string): RollingWindow | null {
  const startDate = parseDateString(startDateStr)
  const endDate = parseDateString(endDateStr)

  const calendarMonths = getCalendarMonthsSpan(startDate, endDate)
  if (calendarMonths) {
    return { amount: calendarMonths, unit: 'months' }
  }

  const rollingMonths = getRollingMonthsDifference(startDate, endDate)
  if (rollingMonths) {
    return { amount: rollingMonths, unit: 'months' }
  }

  const days = getDaysDifference(startDate, endDate)
  if (days > 0 && days % 7 === 0) {
    return { amount: days, unit: 'days' }
  }

  return null
}

export function formatCustomRangeLabel(startDateStr?: string, endDateStr?: string): string {
  if (!startDateStr || !endDateStr) {
    return 'Select dates'
  }

  const detectedPeriod = detectPeriodType(startDateStr, endDateStr)
  if (detectedPeriod) {
    const startDate = parseDateString(startDateStr)
    return getPeriodRange(detectedPeriod, startDate).displayLabel
  }

  const startDate = parseDateString(startDateStr)
  const endDate = parseDateString(endDateStr)

  if (isSameDay(startDate, endDate)) {
    const day = startDate.getDate()
    const month = formatShortMonth(startDate)
    const year = startDate.getFullYear()
    return `${day} ${month} ${year}`
  }

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
