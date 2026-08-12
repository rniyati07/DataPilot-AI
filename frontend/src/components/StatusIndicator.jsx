import Logo from './Logo'

// Polished "thinking" state: DataPilot avatar + animated dots + honest label.
// The request is still in flight — nothing is faked until it resolves.
export default function StatusIndicator({ label = 'DataPilot is analyzing your data…' }) {
  return (
    <div
      className="animate-fade-in flex items-start gap-3"
      role="status"
      aria-live="polite"
    >
      <Logo size={30} />
      <div className="glass-card flex items-center gap-3 rounded-2xl rounded-bl-sm px-4 py-3">
        <span className="flex gap-1.5" aria-hidden="true">
          <span className="h-1.5 w-1.5 animate-typing rounded-full bg-brand-cyan" />
          <span
            className="h-1.5 w-1.5 animate-typing rounded-full bg-brand-indigo"
            style={{ animationDelay: '0.15s' }}
          />
          <span
            className="h-1.5 w-1.5 animate-typing rounded-full bg-brand-violet"
            style={{ animationDelay: '0.3s' }}
          />
        </span>
        <span className="text-sm text-slate-400">{label}</span>
      </div>
    </div>
  )
}
