import { ArrowUp } from 'lucide-react'

// Fixed composer at the bottom of the chat column. Sends real requests;
// disabled while a turn is in flight.
export default function ChatInput({ value, onChange, onSubmit, disabled }) {
  const canSubmit = value.trim().length > 0 && !disabled

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (canSubmit) onSubmit(value)
    }
  }

  return (
    <div className="shrink-0 border-t border-white/5 bg-ink-900/40 p-3 backdrop-blur-xl sm:p-4">
      <form
        onSubmit={(event) => {
          event.preventDefault()
          if (canSubmit) onSubmit(value)
        }}
        className="mx-auto flex max-w-3xl items-end gap-2"
      >
        <div className="flex flex-1 items-center rounded-2xl border border-white/10 bg-white/[0.04] px-4 transition focus-within:border-brand-indigo/50 focus-within:bg-white/[0.06] focus-within:ring-2 focus-within:ring-brand-indigo/20">
          <textarea
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your data anything…"
            rows={1}
            className="max-h-32 w-full resize-none bg-transparent py-3.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
            aria-label="Message QueryVista"
          />
        </div>
        <button
          type="submit"
          disabled={!canSubmit}
          aria-label="Send message"
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-[0_4px_16px_rgb(99_102_241_/_0.4)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-35"
        >
          <ArrowUp className="h-5 w-5" />
        </button>
      </form>
      <p className="mx-auto mt-2 hidden max-w-3xl px-2 text-center text-[11px] text-slate-600 sm:block">
        Read-only — QueryVista can only query your database, never modify it.
      </p>
    </div>
  )
}
