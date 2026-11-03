import { formatDisplayDate, formatTime } from '../utils/datetime'

export default function BookingModal({
  slot,
  date,
  userName,
  email,
  setEmail,
  onClose,
  onSubmit,
  isSubmitting,
  modalError,
  setModalError,
}) {
  if (!slot) return null

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 sm:p-7 border border-slate-100 space-y-5 animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-start justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Confirm Slot Booking</h3>
            <p className="text-xs text-slate-500">
              Please provide your email to confirm this appointment.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-slate-600 text-lg leading-none p-1 rounded-md hover:bg-slate-100 cursor-pointer disabled:opacity-50"
          >
            ✕
          </button>
        </div>

        {/* Selected Slot Information */}
        <div className="bg-indigo-50/60 rounded-xl p-4 border border-indigo-100 space-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Consultant Slot:</span>
            <span className="font-bold text-indigo-950">
              {formatTime(slot.start)} - {formatTime(slot.end)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Date:</span>
            <span className="font-semibold text-slate-800">{formatDisplayDate(date)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-500">Booking For:</span>
            <span className="font-semibold text-slate-800">{userName}</span>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="modalEmail" className="block text-xs font-semibold text-slate-700 mb-1.5">
              Email Address <span className="text-rose-500">*</span>
            </label>
            <input
              id="modalEmail"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setModalError('')
              }}
              placeholder="e.g. yourname@example.com"
              autoFocus
              required
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
            <p className="mt-1 text-[11px] text-slate-500">
              Required by the booking system for confirmation and verification.
            </p>
          </div>

          {/* Soft Warnings / Booking Policy Notice */}
          <div className="rounded-xl bg-amber-50/90 border border-amber-200/80 p-3.5 text-xs text-amber-900 space-y-1.5">
            <div className="flex items-center gap-1.5 font-bold text-amber-950">
              <svg className="w-4 h-4 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>Important Booking Guidelines:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-800/95 pl-1 leading-relaxed">
              <li>
                <strong className="font-semibold">Maximum 2 active slots:</strong> Each user can hold at most 2 active upcoming bookings concurrently.
              </li>
              <li>
                <strong className="font-semibold">2-Hour cancellation notice:</strong> Bookings can only be cancelled up to 2 hours before the slot begins.
              </li>
            </ul>
          </div>

          {/* Modal Error */}
          {modalError && (
            <div className="rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700 flex items-start gap-2">
              <svg className="w-4 h-4 mt-0.5 shrink-0 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span>{modalError}</span>
            </div>
          )}

          {/* Modal Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 border border-slate-200 transition-all cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-500/20 active:scale-[0.99] transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                  </svg>
                  Booking...
                </>
              ) : (
                'Confirm & Book Slot'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
