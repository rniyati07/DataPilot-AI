import { MessageSquarePlus, Upload, Wifi, WifiOff } from 'lucide-react'
import Logo from './Logo'

// Dashboard header: the brand (on mobile, where the sidebar is hidden), the
// real active-database connection pill, and quick actions.
export default function TopBar({ database, dbState, onNewChat, onBackHome, onUploadClick }) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-white/5 bg-ink-900/40 px-4 backdrop-blur-xl sm:px-5">
      <div className="flex min-w-0 items-center gap-3">
        {/* Mobile-only brand + new-chat (sidebar is hidden below md) */}
        <button
          type="button"
          onClick={onBackHome}
          className="md:hidden"
          aria-label="Back to home"
        >
          <Logo size={28} />
        </button>
        <button
          type="button"
          onClick={onNewChat}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-slate-200 transition hover:border-brand-cyan/40 hover:bg-white/10 md:hidden"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New
        </button>

        {/* Connection pill — real active database from the backend */}
        {dbState === 'ready' && database ? (
          <span
            className="inline-flex min-w-0 items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300"
            title={database.name}
          >
            <Wifi className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">Connected to {database.name}</span>
          </span>
        ) : dbState === 'loading' ? (
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-500" />
            Checking database…
          </span>
        ) : (
          <span className="inline-flex items-center gap-2 rounded-full border border-amber-400/25 bg-amber-400/10 px-3 py-1.5 text-xs font-medium text-amber-300">
            <WifiOff className="h-3.5 w-3.5" />
            Backend unreachable
          </span>
        )}
      </div>

      {/* Upload lives in the sidebar's Active Database card, so the header
          stays clean. Below md the sidebar is hidden, so the control is
          mirrored here — the only place it would otherwise be unreachable. */}
      <div className="flex items-center gap-2 md:hidden">
        <button
          type="button"
          onClick={onUploadClick}
          className="focus-ring inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-slate-300 transition hover:border-brand-cyan/40 hover:bg-white/10"
          aria-label="Upload database"
        >
          <Upload className="h-4 w-4" />
          <span className="hidden sm:inline">Upload</span>
        </button>
      </div>
    </header>
  )
}
