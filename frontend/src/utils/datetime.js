export function formatDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatDisplayDate(dateStr) {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatTime(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function formatDateTime(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function isMoreThanTwoHoursAway(slotStartIso) {
  if (!slotStartIso) return false
  const slotTime = new Date(slotStartIso).getTime()
  const twoHoursFromNow = Date.now() + 2 * 60 * 60 * 1000
  return slotTime >= twoHoursFromNow
}

export function isWeekend(dateStr) {
  if (!dateStr) return false
  const [year, month, day] = dateStr.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.getDay() === 0 || d.getDay() === 6
}

export function generate14DaysWindow() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const list = []
  for (let i = 0; i < 14; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    const dateStr = formatDate(d)
    const isWeekend = d.getDay() === 0 || d.getDay() === 6
    list.push({
      dateStr,
      label:
        i === 0
          ? 'Today'
          : i === 1
          ? 'Tomorrow'
          : d.toLocaleDateString(undefined, {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            }),
      dayName: d.toLocaleDateString(undefined, { weekday: 'short' }),
      dayNum: d.getDate(),
      month: d.toLocaleDateString(undefined, { month: 'short' }),
      isWeekend,
    })
  }

  return {
    minDate: list[0].dateStr,
    maxDate: list[list.length - 1].dateStr,
    availableDateList: list,
  }
}

export function generateIdempotencyKey() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `frontend-${crypto.randomUUID()}`
  }
  return `frontend-${Date.now()}`
}
