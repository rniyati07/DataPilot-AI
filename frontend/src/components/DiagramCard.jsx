import { Network } from 'lucide-react'
import DiagramRenderer from './DiagramRenderer'

// Diagram card: renders the backend's Mermaid syntax. The response envelope
// carries only the syntax string, so the kind badge is inferred from the
// actual diagram content — a truthful read of what was returned.
function inferKind(diagram) {
  if (!diagram) return 'Diagram'
  if (diagram.includes('erDiagram')) return 'Entity-relationship'
  if (diagram.includes('flowchart') || diagram.includes('graph ')) return 'Process flow'
  return 'Diagram'
}

export default function DiagramCard({ diagram, isLight }) {
  if (!diagram) return null

  return (
    <div className="overflow-hidden rounded-xl border border-white/8">
      <div className="flex items-center gap-2 border-b border-white/6 bg-white/[0.03] px-3.5 py-2">
        <Network className="h-3.5 w-3.5 text-brand-cyan" />
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Diagram
        </span>
        <span className="ml-auto rounded-full border border-brand-indigo/30 bg-brand-indigo/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-indigo">
          {inferKind(diagram)}
        </span>
      </div>
      <div className="p-2">
        <DiagramRenderer diagram={diagram} isLight={isLight} />
      </div>
    </div>
  )
}
