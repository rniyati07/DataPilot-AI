// Real Mermaid rendering lands in Batch 2 (Phase 10). Batch 1 only needs the
// component to exist and safely no-op when there is no diagram syntax yet.
export default function DiagramRenderer({ diagram }) {
  if (!diagram) return null

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-500">
      Diagram rendering will be available in Batch 2.
    </div>
  )
}
