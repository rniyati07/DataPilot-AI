import { AlertTriangle, X } from 'lucide-react'

// Transport-level failure (backend unreachable, HTTP error). Structured
// agent errors inside a response envelope are styled in the message cards.
export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null

  return (
    <div className="animate-fade-in mx-auto flex max-w-3xl items-start justify-between gap-3 rounded-xl border border-red-400/25 bg-red-400/10 px-4 py-3 text-sm text-red-300">
      <div className="flex items-start gap-2.5">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{message}</span>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded-md p-1 text-red-400/80 transition hover:bg-white/5 hover:text-red-200"
          aria-label="Dismiss error"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
