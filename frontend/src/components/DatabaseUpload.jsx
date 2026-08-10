import { useEffect, useRef, useState } from 'react'
import ErrorBanner from './ErrorBanner'
import { getCurrentDatabase, uploadDatabase, ApiError } from '../api/client'

export default function DatabaseUpload() {
  const [database, setDatabase] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    getCurrentDatabase()
      .then(setDatabase)
      .catch(() => setError('Could not reach the backend to check the active database.'))
      .finally(() => setIsLoading(false))
  }, [])

  async function handleFileChange(event) {
    const file = event.target.files?.[0]
    event.target.value = '' // allow re-selecting the same file later
    if (!file) return

    setIsUploading(true)
    setError(null)
    try {
      const result = await uploadDatabase(file)
      setDatabase(result)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-700">Database</h2>

      {isLoading ? (
        <p className="text-sm text-slate-400">Checking active database…</p>
      ) : (
        database && (
          <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <span className="font-medium text-slate-800">{database.name}</span>
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              {database.source === 'upload' ? 'Connected (uploaded)' : 'Connected (demo)'}
            </span>
          </div>
        )
      )}

      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className="w-full rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
      >
        {isUploading ? 'Uploading…' : 'Upload SQLite Database'}
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".db,.sqlite,.sqlite3"
        onChange={handleFileChange}
        className="hidden"
      />

      <ErrorBanner message={error} onDismiss={() => setError(null)} />
    </div>
  )
}
