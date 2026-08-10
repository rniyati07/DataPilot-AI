// Real Plotly rendering lands in Batch 2 (Phase 8). Batch 1 only needs the
// component to exist and safely no-op when there is no chart spec yet.
export default function ChartRenderer({ chart }) {
  if (!chart) return null

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-500">
      Chart rendering will be available in Batch 2.
    </div>
  )
}
