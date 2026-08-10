export default function SqlPanel({ sql }) {
  if (!sql) return null

  return (
    <details className="rounded-md border border-slate-200 bg-slate-50 text-sm">
      <summary className="cursor-pointer select-none px-3 py-2 font-medium text-slate-600">
        Generated SQL
      </summary>
      <pre className="overflow-x-auto px-3 pb-3 text-slate-800">
        <code>{sql}</code>
      </pre>
    </details>
  )
}
