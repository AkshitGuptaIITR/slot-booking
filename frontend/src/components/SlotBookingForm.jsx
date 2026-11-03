import { formatDisplayDate } from '../utils/datetime'

export default function SlotBookingForm({
  userName,
  setUserName,
  slotDate,
  onDateChange,
  onSubmit,
  loadingSlots,
  minDate,
  maxDate,
  availableDateList,
}) {
  const selectedDateItem = availableDateList.find((i) => i.dateStr === slotDate)

  return (
    <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/80 p-6 sm:p-8">
      <form onSubmit={onSubmit} className="space-y-5">
        {/* User Name Input */}
        <div>
          <label htmlFor="userName" className="block text-sm font-medium text-slate-700 mb-1.5">
            User Name <span className="text-rose-500">*</span>
          </label>
          <input
            id="userName"
            type="text"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            placeholder="e.g. AlexMorgan or user_123"
            className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-sm transition-all"
            required
          />
          <p className="mt-1 text-xs text-slate-500">
            Identifies your session and tracks your bookings.
          </p>
        </div>

        {/* Slot Date Input */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="slotDate" className="block text-sm font-medium text-slate-700">
              Slot Date <span className="text-rose-500">*</span>
            </label>
            <span className="text-xs font-medium text-indigo-600">
              Allowed: {minDate} to {maxDate}
            </span>
          </div>

          <input
            id="slotDate"
            type="date"
            min={minDate}
            max={maxDate}
            value={slotDate}
            onChange={(e) => onDateChange(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-sm transition-all bg-white"
            required
          />

          {/* Quick Select Buttons (14 Days) */}
          <div className="mt-3">
            <p className="text-xs font-medium text-slate-600 mb-2">
              Select from next 14 days (Monday to Friday only):
            </p>
            <div className="grid grid-cols-4 sm:grid-cols-7 gap-1.5 max-h-44 overflow-y-auto p-1.5 border border-slate-100 rounded-xl bg-slate-50/60">
              {availableDateList.map((item) => {
                const isSelected = slotDate === item.dateStr
                return (
                  <button
                    type="button"
                    key={item.dateStr}
                    disabled={item.isWeekend}
                    onClick={() => onDateChange(item.dateStr)}
                    className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg text-xs font-medium transition-all ${
                      item.isWeekend
                        ? 'bg-slate-100/70 text-slate-400 border border-slate-200 cursor-not-allowed opacity-60'
                        : isSelected
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20 scale-[1.02] cursor-pointer'
                        : 'bg-white text-slate-700 hover:bg-indigo-50 border border-slate-200 cursor-pointer'
                    }`}
                    title={item.isWeekend ? `${item.dateStr} (Weekend - Closed)` : item.dateStr}
                  >
                    <span className="text-[10px] uppercase tracking-wider opacity-80">
                      {item.dayName}
                    </span>
                    <span className="text-sm font-bold">{item.dayNum}</span>
                    <span className="text-[9px] opacity-75">
                      {item.isWeekend ? 'Closed' : item.month}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {slotDate && (
            <div className="mt-2 text-xs text-slate-600 flex items-center justify-between">
              <span>
                Selected: <strong className="text-slate-900">{formatDisplayDate(slotDate)}</strong>
              </span>
              {selectedDateItem?.isWeekend && (
                <span className="text-amber-700 font-medium bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Closed on Weekends
                </span>
              )}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loadingSlots}
          className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-500/25 hover:bg-indigo-700 active:scale-[0.99] transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
        >
          {loadingSlots ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
              Checking Available Slots...
            </>
          ) : (
            'Find Available Slots'
          )}
        </button>
      </form>
    </div>
  )
}
