export async function fetchSlots(userId, date) {
  const response = await fetch(`/api/slots?date=${encodeURIComponent(date)}`, {
    headers: {
      'X-User-Id': userId,
    },
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.error?.message || `Failed to fetch slots (Status ${response.status})`)
  }

  return response.json()
}

export async function fetchUserBookings(userId) {
  const response = await fetch('/api/bookings', {
    headers: {
      'X-User-Id': userId,
    },
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.error?.message || `Failed to fetch bookings (Status ${response.status})`)
  }

  return response.json()
}

export async function createBooking(userId, slotStart, name, email, idempotencyKey) {
  const response = await fetch('/api/bookings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId,
      'Idempotency-Key': idempotencyKey,
    },
    body: JSON.stringify({
      slot_start: slotStart,
      name,
      email,
    }),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.error?.message || 'Failed to complete booking.')
  }

  return data
}

export async function cancelBooking(userId, bookingId) {
  const response = await fetch(`/api/bookings/${bookingId}`, {
    method: 'DELETE',
    headers: {
      'X-User-Id': userId,
    },
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.error?.message || 'Failed to cancel booking.')
  }

  return data
}
