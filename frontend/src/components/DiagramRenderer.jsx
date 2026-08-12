// Real Mermaid rendering (Phase 10). The backend's generate_flowchart tool
// returns validated Mermaid syntax; this component renders it with the mermaid
// package (Architecture Rule 10). securityLevel: 'strict' sanitizes the SVG.
//
// Theming: mermaid v11's `erBox` shape fills each attribute row with
//   fill: isEven ? rowEven : rowOdd
// (verified in mermaid/dist/chunks/mermaid.core/chunk-QR6OTTB3.mjs). Those two
// variables must be set explicitly: under `theme: 'base'` mermaid derives
// `rowOdd = lighten(mainBkg, 75)`, which turns a dark navy surface into a
// near-white row. Combined with a light `nodeTextColor` that produced light
// text on a light fill — the invisible id / PK / FK / sku rows.
//
// Note that mermaid paints every attribute row from these two variables and
// uses one text colour for all of them, so contrast is guaranteed by keeping
// the row fills and the text colour on the same side of the light/dark divide
// per theme, rather than by colouring individual rows.
//
// Sizing: useMaxWidth is off so a large ER diagram renders at its natural size
// and is explored by scrolling, rather than being shrunk until it is illegible.
import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

let renderCounter = 0
let initializedTheme = null

function themeVariables(isLight) {
  return isLight
    ? {
        background: 'transparent',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: '13px',
        mainBkg: '#ffffff',
        primaryColor: '#ffffff',
        primaryTextColor: '#0f172a',
        primaryBorderColor: '#cbd5e1',
        secondaryColor: '#f1f5f9',
        tertiaryColor: '#f8fafc',
        nodeBorder: '#cbd5e1',
        nodeTextColor: '#0f172a',
        clusterBkg: '#f8fafc',
        clusterBorder: '#e2e8f0',
        textColor: '#0f172a',
        lineColor: '#64748b',
        edgeLabelBackground: '#ffffff',
        // ER attribute rows — light fills to pair with the dark text above.
        rowOdd: '#f1f5f9',
        rowEven: '#ffffff',
      }
    : {
        background: 'transparent',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: '13px',
        mainBkg: '#141d3a',
        primaryColor: '#141d3a',
        primaryTextColor: '#e2e8f0',
        primaryBorderColor: 'rgba(148, 163, 184, 0.35)',
        secondaryColor: '#0f1730',
        tertiaryColor: '#0b1224',
        nodeBorder: 'rgba(148, 163, 184, 0.45)',
        // Drives ER attribute-row text.
        nodeTextColor: '#e2e8f0',
        clusterBkg: 'rgba(255, 255, 255, 0.03)',
        clusterBorder: 'rgba(148, 163, 184, 0.25)',
        textColor: '#e2e8f0',
        lineColor: '#94a3b8',
        edgeLabelBackground: '#0b1224',
        // ER attribute rows. Without these, `base` derives rowOdd from mainBkg
        // as a near-white fill, which hides the light row text entirely.
        // Two close navies keep the banding readable but subtle.
        rowOdd: '#16203f',
        rowEven: '#0e1730',
      }
}

function ensureInitialized(isLight) {
  const theme = isLight ? 'light' : 'dark'
  if (initializedTheme === theme) return
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    themeVariables: themeVariables(isLight),
    // Natural size + scrollable viewport beats shrink-to-fit for big schemas.
    er: { useMaxWidth: false, diagramPadding: 16, entityPadding: 12 },
    flowchart: { useMaxWidth: false, htmlLabels: false, padding: 12 },
  })
  initializedTheme = theme
}

export default function DiagramRenderer({ diagram, isLight = false }) {
  const containerRef = useRef(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (!diagram) return

    let cancelled = false
    ensureInitialized(isLight)
    setFailed(false)
    const renderId = `dp-diagram-${renderCounter++}`

    mermaid
      .render(renderId, diagram)
      .then(({ svg }) => {
        if (!cancelled && containerRef.current) containerRef.current.innerHTML = svg
      })
      .catch(() => {
        // Invalid Mermaid must not take down the rest of the response.
        if (cancelled) return
        if (containerRef.current) containerRef.current.innerHTML = ''
        setFailed(true)
      })

    return () => {
      cancelled = true
    }
  }, [diagram, isLight])

  if (!diagram) return null

  if (failed) {
    return (
      <p role="status" className="px-3 py-8 text-center text-sm text-amber-300/90">
        This diagram could not be rendered. The explanation above still describes it.
      </p>
    )
  }

  return (
    // Bounded viewport that scrolls in both axes, so a wide schema keeps its
    // readable scale instead of being shrunk to fit. Extra end padding keeps
    // the scrollbars from sitting on top of the last entity.
    <div
      className="dp-diagram focus-ring max-h-[68vh] overflow-auto rounded-lg"
      tabIndex={0}
      role="group"
      aria-label="Entity relationship diagram. Scroll horizontally and vertically to explore."
    >
      <div ref={containerRef} className="flex min-w-max justify-center p-3 pb-5 pr-5" />
    </div>
  )
}
