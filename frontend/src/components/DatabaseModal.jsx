import { useRef, useState } from 'react'
import { CheckCircle2, Database, Upload, X } from 'lucide-react'
import { uploadDatabase, ApiError } from '../api/client'

// Database manager modal — replaces the old inline DatabaseUpload card.
// Reads and updates the real backend's session-scoped active database.
export default function DatabaseModal({ open, database, onClose, onDatabaseChange }) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  if (!open) return null

  async function handleFileChange(event) {
    const file = event.target.files?.[0]
    event.target.value = '' // allow re-selecting the same file later
    if (!file) return

    setIsUploading(true)
    setError(null)
    try {
      const result = await uploadDatabase(file)
      onDatabaseChange(result)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/70 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Manage database"
      onClick={onClose}
    >
      <div
        className="glass-card w-full max-w-md animate-fade-up rounded-2xl p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-brand-indigo/15 ring-1 ring-brand-indigo/25">
              <Database className="h-4.5 w-4.5 text-brand-cyan" />
            </span>
            <div>
              <h2 className="text-base font-semibold text-white">Database</h2>
              <p className="text-xs text-slate-400">Session-scoped, stored on the server</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-5 rounded-xl border border-white/8 bg-white/[0.03] p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Active database
          </p>
          <div className="mt-2 flex items-center gap-2.5">
            <CheckCircle2 className="h-4.5 w-4.5 shrink-0 text-emerald-400" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-200">
                {database ? database.name : 'No active database'}
              </p>
              <p className="text-xs text-slate-500">
                {database?.source === 'upload'
                  ? 'Uploaded by you'
                  : 'Built-in demo database'}
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-white/[0.03] px-4 py-3 text-sm font-medium text-slate-200 transition hover:border-brand-cyan/50 hover:bg-white/5 disabled:opacity-50"
        >
          <Upload className="h-4 w-4" />
          {isUploading ? 'Uploading…' : 'Upload a SQLite database'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".db,.sqlite,.sqlite3"
          onChange={handleFileChange}
          className="hidden"
        />
        <p className="mt-2 text-center text-[11px] text-slate-500">
          .db · .sqlite · .sqlite3 — replaces the active database for this session
        </p>

        {error && (
          <div className="mt-4 rounded-lg border border-red-400/25 bg-red-400/10 px-3 py-2.5 text-sm text-red-300">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
