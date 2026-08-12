import { Table2 } from 'lucide-react'

// Polished result table (frontend batch §Batch 4): dark surface, sticky
// header, subtle row separation, right-aligned numeric columns, and a clear
// empty state. Data comes straight from the API response — never invented.
function isNumeric(value) {
  return typeof value === 'number' && !Number.isNaN(value)
}

export default function ResultTable({ columns, rows }) {
  if (!columns || columns.length === 0) return null

  const numericColumns = columns.map((_, index) =>
    rows.every((row) => isNumeric(row[index]) || row[index] === null),
  )

  return (
    <div className="overflow-hidden rounded-xl border border-white/8">
      <div className="flex items-center gap-2 border-b border-white/6 bg-white/[0.03] px-3.5 py-2">
        <Table2 className="h-3.5 w-3.5 text-brand-cyan" />
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Results
        </span>
        <span className="ml-auto text-[11px] text-slate-500">
          {rows.length} row{rows.length === 1 ? '' : 's'} · {columns.length} column
          {columns.length === 1 ? '' : 's'}
        </span>
      </div>

      {rows.length === 0 ? (
        <p className="px-4 py-6 text-center text-sm text-slate-500">
          No rows returned for this query.
        </p>
      ) : (
        <div className="focus-ring max-h-96 overflow-auto" tabIndex={0}>
          <table className="w-full border-collapse text-[13px]">
            <caption className="sr-only">
              Query result: {rows.length} rows by {columns.length} columns
            </caption>
            <thead className="sticky top-0 z-10 bg-ink-850">
              <tr>
                {columns.map((column, index) => (
                  // eslint-disable-next-line react/no-array-index-key
                  <th
                    key={`${column}-${index}`}
                    scope="col"
                    className={`whitespace-nowrap border-b border-white/8 px-3.5 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400 ${
                      numericColumns[index] ? 'text-right' : 'text-left'
                    }`}
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.05]">
              {rows.map((row, rowIndex) => (
                // eslint-disable-next-line react/no-array-index-key
                <tr key={rowIndex} className="transition-colors hover:bg-white/[0.04]">
                  {row.map((cell, cellIndex) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <td
                      key={cellIndex}
                      className={`whitespace-nowrap px-3.5 py-2.5 text-slate-300 ${
                        numericColumns[cellIndex] ? 'text-right tabular-nums' : 'text-left'
                      }`}
                    >
                      {cell === null || cell === undefined ? (
                        <span className="text-slate-600">—</span>
                      ) : (
                        String(cell)
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
