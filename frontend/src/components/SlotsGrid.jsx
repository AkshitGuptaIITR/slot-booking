import { formatDisplayDate, formatTime, isWeekend } from '../utils/datetime'

export default function SlotsGrid({
  userName,
  date,
  slots,
  loadingSlots,
  onRefresh,
  onSelectSlot,
  hasError,
}) {
  return (
    <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/80 p-6 sm:p-8 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Available Slots</h2>
          <p className="text-xs text-slate-500">
            User: <span className="font-semibold text-slate-700">{userName}</span> | Date:{' '}
            <span className="font-semibold text-slate-700">{formatDisplayDate(date)}</span>
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="text-xs text-indigo-600 hover:text-indigo-800 font-medium inline-flex items-center gap-1 self-start sm:self-auto cursor-pointer"
        >
          ↻ Refresh Slots
        </button>
      </div>

      {loadingSlots ? (
        <div className="py-8 text-center text-sm text-slate-500">
          Loading slots from server...
        </div>
      ) : slots.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {slots.map((slot, idx) => (
            <button
              key={slot.start || idx}
              type="button"
              disabled={!slot.available}
              onClick={() => onSelectSlot(slot)}
              className={`p-3 rounded-xl border text-center transition-all ${
                slot.available
                  ? 'border-indigo-200 bg-indigo-50/40 hover:bg-indigo-600 hover:text-white hover:border-indigo-600 text-indigo-900 shadow-sm cursor-pointer'
                  : 'border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed line-through opacity-70'
              }`}
            >
              <div className="text-xs font-semibold">
                {formatTime(slot.start)} - {formatTime(slot.end)}
              </div>
              <div className="text-[10px] mt-1 font-medium">
                {slot.available ? 'Click to Book' : 'Booked'}
              </div>
            </button>
          ))}
        </div>
      ) : (
        !loadingSlots && (
          <div className="py-6 text-center text-sm text-slate-500">
            {hasError
              ? 'No slots displayed due to error.'
              : isWeekend(date)
              ? 'The consultant is closed on weekends (Monday to Friday only).'
              : 'No slots available for this date.'}
          </div>
        )
      )}
    </div>
  )
}
