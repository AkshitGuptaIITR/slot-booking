import { useState, useMemo, useRef } from 'react'

import Header from './components/Header'
import AlertBanner from './components/AlertBanner'
import SlotBookingForm from './components/SlotBookingForm'
import MyBookings from './components/MyBookings'
import SlotsGrid from './components/SlotsGrid'
import BookingModal from './components/BookingModal'

import {
  generate14DaysWindow,
  generateIdempotencyKey,
  formatTime,
  formatDisplayDate,
  isMoreThanTwoHoursAway,
} from './utils/datetime'
import {
  fetchSlots,
  fetchUserBookings,
  createBooking,
  cancelBooking,
} from './services/api'

export default function App() {
  // Input state
  const [userName, setUserName] = useState('')
  const [slotDate, setSlotDate] = useState('')

  // Active session state
  const [submittedUser, setSubmittedUser] = useState(null)
  const [submittedDate, setSubmittedDate] = useState(null)
  const [slots, setSlots] = useState([])
  const [userBookings, setUserBookings] = useState([])

  // Async load states
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [loadingBookings, setLoadingBookings] = useState(false)
  const [cancellingBookingId, setCancellingBookingId] = useState(null)

  // Booking confirmation modal state
  const [activeSlotModal, setActiveSlotModal] = useState(null)
  const [bookingEmail, setBookingEmail] = useState('')
  const [isSubmittingBooking, setIsSubmittingBooking] = useState(false)
  const [modalError, setModalError] = useState('')

  // Feedback notifications
  const [errorMsg, setErrorMsg] = useState('')
  const [bookingSuccessMsg, setBookingSuccessMsg] = useState('')

  // Request race-condition guard
  const activeFetchIdRef = useRef(0)
  // Track which user's bookings have already been loaded to prevent refetching repeatedly
  const fetchedBookingsUserRef = useRef(null)

  // 14-day booking window calculation
  const { minDate, maxDate, availableDateList } = useMemo(() => generate14DaysWindow(), [])

  // Slot fetching
  const handleFetchSlots = async (user, date) => {
    const fetchId = ++activeFetchIdRef.current
    setLoadingSlots(true)
    setErrorMsg('')

    try {
      const data = await fetchSlots(user, date)
      if (fetchId === activeFetchIdRef.current) {
        setSlots(data)
      }
    } catch (err) {
      if (fetchId === activeFetchIdRef.current) {
        setErrorMsg(err.message || 'Failed to fetch slots.')
        setSlots([])
      }
    } finally {
      if (fetchId === activeFetchIdRef.current) {
        setLoadingSlots(false)
      }
    }
  }

  // Booking list fetching (only fetched once per user unless forced by booking/cancellation)
  const handleFetchBookings = async (user, force = false) => {
    if (!force && fetchedBookingsUserRef.current === user) {
      return
    }

    setLoadingBookings(true)
    try {
      const data = await fetchUserBookings(user)
      setUserBookings(data)
      fetchedBookingsUserRef.current = user
    } catch {
      // Non-fatal background fetch failure
    } finally {
      setLoadingBookings(false)
    }
  }

  // Date selection (instantly fetches slots if user name exists)
  const handleDateChange = (val) => {
    setSlotDate(val)
    setErrorMsg('')
    setBookingSuccessMsg('')

    if (!val) return

    if (val < minDate || val > maxDate) {
      setErrorMsg(`Slot date must be between ${minDate} and ${maxDate} (within 14 days from today).`)
      return
    }

    const trimmedUser = userName.trim()
    if (!trimmedUser) {
      setErrorMsg('Please enter your user name to view available slots.')
      return
    }

    setSubmittedUser(trimmedUser)
    setSubmittedDate(val)
    handleFetchSlots(trimmedUser, val)
    handleFetchBookings(trimmedUser)
  }

  // Explicit form submission
  const handleSubmit = (e) => {
    e.preventDefault()
    setErrorMsg('')
    setBookingSuccessMsg('')

    const trimmedUser = userName.trim()
    if (!trimmedUser) {
      setErrorMsg('Please enter your user name.')
      return
    }

    if (!slotDate) {
      setErrorMsg('Please select a slot date.')
      return
    }

    if (slotDate < minDate || slotDate > maxDate) {
      setErrorMsg(`Slot date must be between ${minDate} and ${maxDate} (within 14 days from today).`)
      return
    }

    setSubmittedUser(trimmedUser)
    setSubmittedDate(slotDate)
    handleFetchSlots(trimmedUser, slotDate)
    handleFetchBookings(trimmedUser)
  }

  // Open booking modal
  const handleOpenBookingModal = (slot) => {
    setActiveSlotModal(slot)
    setModalError('')
    setErrorMsg('')
    setBookingSuccessMsg('')
  }

  // Close booking modal
  const handleCloseModal = () => {
    if (isSubmittingBooking) return
    setActiveSlotModal(null)
    setModalError('')
  }

  // Submit booking from modal
  const handleConfirmBooking = async (e) => {
    e.preventDefault()
    if (!activeSlotModal || !submittedUser) return

    setModalError('')
    const trimmedEmail = bookingEmail.trim()
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

    if (!trimmedEmail) {
      setModalError('Email is required to confirm this booking.')
      return
    }

    if (!emailRegex.test(trimmedEmail)) {
      setModalError('Please enter a valid email address (e.g. name@example.com).')
      return
    }

    setIsSubmittingBooking(true)
    try {
      const idempotencyKey = generateIdempotencyKey()
      await createBooking(
        submittedUser,
        activeSlotModal.start,
        submittedUser,
        trimmedEmail,
        idempotencyKey
      )

      setBookingSuccessMsg(
        `Slot successfully booked for ${formatTime(activeSlotModal.start)} on ${formatDisplayDate(submittedDate)}!`
      )
      setActiveSlotModal(null)
      setBookingEmail('')
      handleFetchSlots(submittedUser, submittedDate)
      handleFetchBookings(submittedUser, true)
    } catch (err) {
      setModalError(err.message || 'Could not complete the booking. Please try again.')
    } finally {
      setIsSubmittingBooking(false)
    }
  }

  // Cancel booking
  const handleCancelBooking = async (bookingId, slotStart) => {
    if (!submittedUser) return
    setErrorMsg('')
    setBookingSuccessMsg('')

    if (!isMoreThanTwoHoursAway(slotStart)) {
      setErrorMsg('Bookings cannot be cancelled within 2 hours of the slot start time.')
      return
    }

    setCancellingBookingId(bookingId)
    try {
      await cancelBooking(submittedUser, bookingId)
      setBookingSuccessMsg('Booking cancelled successfully!')
      handleFetchBookings(submittedUser, true)
      if (submittedDate) {
        handleFetchSlots(submittedUser, submittedDate)
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to cancel booking.')
    } finally {
      setCancellingBookingId(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50/30 to-slate-100 py-10 px-4 sm:px-6 lg:px-8 flex flex-col items-center">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <Header />

        {/* Global Feedback Banners */}
        <AlertBanner type="error" message={errorMsg} />
        <AlertBanner type="success" message={bookingSuccessMsg} />

        {/* First Page Form */}
        <SlotBookingForm
          userName={userName}
          setUserName={setUserName}
          slotDate={slotDate}
          onDateChange={handleDateChange}
          onSubmit={handleSubmit}
          loadingSlots={loadingSlots}
          minDate={minDate}
          maxDate={maxDate}
          availableDateList={availableDateList}
        />

        {/* My Bookings Section */}
        {submittedUser && (
          <MyBookings
            userName={submittedUser}
            userBookings={userBookings}
            loadingBookings={loadingBookings}
            cancellingBookingId={cancellingBookingId}
            onCancelBooking={handleCancelBooking}
          />
        )}

        {/* Slot Results Section */}
        {submittedUser && submittedDate && (
          <SlotsGrid
            userName={submittedUser}
            date={submittedDate}
            slots={slots}
            loadingSlots={loadingSlots}
            onRefresh={() => handleFetchSlots(submittedUser, submittedDate)}
            onSelectSlot={handleOpenBookingModal}
            hasError={Boolean(errorMsg)}
          />
        )}
      </div>

      {/* Confirmation & Email Modal */}
      <BookingModal
        slot={activeSlotModal}
        date={submittedDate}
        userName={submittedUser}
        email={bookingEmail}
        setEmail={setBookingEmail}
        onClose={handleCloseModal}
        onSubmit={handleConfirmBooking}
        isSubmitting={isSubmittingBooking}
        modalError={modalError}
        setModalError={setModalError}
      />
    </div>
  )
}
