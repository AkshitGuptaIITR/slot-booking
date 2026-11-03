export default function Header() {
  return (
    <div className="text-center space-y-2">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700">
        <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"></span>
        14-Day Booking Window • All 7 Days Available
      </div>
      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
        Consultant Slot Booking
      </h1>
      <p className="text-sm sm:text-base text-slate-600">
        Enter your user name and pick a date to check available slots.
      </p>
    </div>
  )
}
