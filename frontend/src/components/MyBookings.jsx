import { formatDateTime, isMoreThanTwoHoursAway } from '../utils/datetime'

export default function MyBookings({
  userName,
  userBookings,
  loadingBookings,
  cancellingBookingId,
  onCancelBooking,
}) {
  return (
    <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/80 p-6 sm:p-8 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h2 className="text-lg font-bold text-slate-900">My Bookings</h2>
          <p className="text-xs text-slate-500">
            Manage active appointments for <span className="font-semibold text-slate-700">{userName}</span>
          </p>
        </div>
        <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
          Cancellation cutoff: ≥ 2 hrs notice
        </span>
      </div>

      {loadingBookings ? (
        <div className="py-4 text-center text-xs text-slate-500">Loading bookings...</div>
      ) : userBookings.length > 0 ? (
        <div className="space-y-2.5">
          {userBookings.map((b) => {
            const isActive = b.status === 'ACTIVE'
            const cancellable = isActive && isMoreThanTwoHoursAway(b.slot_start)

            return (
              <div
                key={b.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">
                      {formatDateTime(b.slot_start)}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        isActive
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {b.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Email: <span className="text-slate-700">{b.email}</span> • ID:{' '}
                    <code className="text-[11px] text-slate-600">{b.id.slice(0, 8)}...</code>
                  </p>
                </div>

                {isActive && (
                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    {cancellable ? (
                      <button
                        type="button"
                        disabled={cancellingBookingId === b.id}
                        onClick={() => onCancelBooking(b.id, b.slot_start)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-600 hover:text-white border border-rose-200 hover:border-rose-600 transition-all cursor-pointer disabled:opacity-50"
                      >
                        {cancellingBookingId === b.id ? 'Cancelling...' : 'Cancel Booking'}
                      </button>
                    ) : (
                      <span
                        className="text-[11px] text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-lg"
                        title="Cannot cancel within 2 hours of slot start time"
                      >
                        Cannot cancel (&lt; 2h notice)
                      </span>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <p className="py-3 text-xs text-slate-500 text-center">
          No active or previous bookings found for this user.
        </p>
      )}
    </div>
  )
}
