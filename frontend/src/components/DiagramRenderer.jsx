// Real Mermaid rendering (Phase 10). The backend's generate_flowchart tool
// returns validated Mermaid syntax; this component renders it with the mermaid
// package (Architecture Rule 10). securityLevel: 'strict' sanitizes the SVG.
import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

let initialized = false
let renderCounter = 0

function ensureInitialized() {
  if (!initialized) {
    mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict' })
    initialized = true
  }
}

export default function DiagramRenderer({ diagram }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!diagram) return

    let cancelled = false
    ensureInitialized()
    const renderId = `dp-diagram-${renderCounter++}`

    mermaid
      .render(renderId, diagram)
      .then(({ svg }) => {
        if (!cancelled && containerRef.current) containerRef.current.innerHTML = svg
      })
      .catch(() => {
        if (!cancelled && containerRef.current) {
          containerRef.current.textContent = 'This diagram could not be rendered.'
        }
      })

    return () => {
      cancelled = true
    }
  }, [diagram])

  if (!diagram) return null

  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white p-2">
      <div ref={containerRef} className="flex justify-center text-sm" />
    </div>
  )
}
