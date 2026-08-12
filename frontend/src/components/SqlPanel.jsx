import { useState } from 'react'
import { Check, ChevronDown, Code2, Copy, ShieldCheck, ShieldAlert } from 'lucide-react'
import SqlCode from './SqlCode'

// Premium "Generated SQL" card (frontend batch §Batch 4). The SQL comes from
// the real API response. "VERIFIED" means the query executed successfully;
// an error-type badge shows when it did not. Copy + collapse are real actions.
export default function SqlPanel({ sql, hasError }) {
  const [copied, setCopied] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  if (!sql) return null

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(sql)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      // Clipboard unavailable — nothing to do, badge stays "Copy".
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-white/8 bg-ink-950/60">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 border-b border-white/6 px-3.5 py-2.5">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-brand-indigo/15 ring-1 ring-brand-indigo/25">
            <Code2 className="h-3.5 w-3.5 text-brand-cyan" />
          </span>
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Generated SQL
          </span>
          {hasError ? (
            <span className="inline-flex items-center gap-1 rounded-full border border-red-400/30 bg-red-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-300">
              <ShieldAlert className="h-3 w-3" />
              Error
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
              <ShieldCheck className="h-3 w-3" />
              Verified
            </span>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={handleCopy}
            className="action-button"
            aria-label="Copy SQL to clipboard"
            title="Copy SQL to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Copy</span>
              </>
            )}
          </button>
          <button
            type="button"
            onClick={() => setCollapsed((value) => !value)}
            className="action-button px-1.5"
            aria-expanded={!collapsed}
            aria-label={collapsed ? 'Expand SQL' : 'Collapse SQL'}
            title={collapsed ? 'Expand SQL' : 'Collapse SQL'}
          >
            <ChevronDown
              className={`h-4 w-4 transition-transform ${collapsed ? '' : 'rotate-180'}`}
            />
          </button>
        </div>
      </div>

      {/* Body */}
      {/* Long statements scroll horizontally rather than wrapping; tabIndex
          keeps that scroll region reachable by keyboard. */}
      {!collapsed && (
        <pre className="focus-ring max-h-80 overflow-auto px-4 py-3" tabIndex={0}>
          <SqlCode sql={sql} />
        </pre>
      )}
    </div>
  )
}
