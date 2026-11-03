export default function AlertBanner({ type, message }) {
  if (!message) return null

  const isError = type === 'error'

  return (
    <div
      className={`rounded-xl p-3 text-xs flex items-start gap-2 ${
        isError
          ? 'bg-rose-50 border border-rose-200 text-rose-700'
          : 'bg-emerald-50 border border-emerald-200 text-emerald-700'
      }`}
    >
      {isError ? (
        <svg
          className="w-4 h-4 mt-0.5 shrink-0 text-rose-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      ) : (
        <svg
          className="w-4 h-4 mt-0.5 shrink-0 text-emerald-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
      )}
      <span>{message}</span>
    </div>
  )
}
