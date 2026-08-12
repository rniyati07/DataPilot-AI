import { useCallback, useRef, useState } from 'react'
import { BarChart3, Download, Loader2 } from 'lucide-react'
import Plotly from 'plotly.js-dist-min'
import ChartRenderer from './ChartRenderer'

const TYPE_LABELS = {
  bar: 'Bar chart',
  line: 'Line chart',
  pie: 'Pie chart',
  scatter: 'Scatter',
}

// Opaque export background: the on-screen chart is transparent so it sits on
// the card, but a transparent PNG is unusable in a viewer whose backdrop
// happens to match the text. Exports get the active theme's surface baked in.
const EXPORT_BG_DARK = '#0b1220'
const EXPORT_BG_LIGHT = '#ffffff'

function fileNameFor(title) {
  const base = (title || 'datapilot-chart')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return base || 'datapilot-chart'
}

// Chart card: renders the backend's real Plotly spec with a labeled header.
// If the backend decided no chart is useful (chart_type 'none'), nothing shows
// — so the download action can never appear without a chart behind it.
export default function ChartCard({ chart, isLight }) {
  const graphRef = useRef(null)
  const [status, setStatus] = useState('idle') // idle | working | failed

  const handleGraphRef = useCallback((node) => {
    graphRef.current = node
  }, [])

  async function handleDownload() {
    const graph = graphRef.current
    if (!graph || status === 'working') return

    setStatus('working')
    const exportBg = isLight ? EXPORT_BG_LIGHT : EXPORT_BG_DARK
    try {
      // Export the live graph's own data/layout — this is the chart actually
      // on screen, not a screenshot of the page. Only the backdrop is swapped
      // so the PNG is legible outside the dark UI.
      const url = await Plotly.toImage(
        {
          data: graph.data,
          layout: { ...graph.layout, paper_bgcolor: exportBg, plot_bgcolor: exportBg },
        },
        {
          format: 'png',
          width: Math.max(graph.offsetWidth || 900, 900),
          height: Math.max(graph.offsetHeight || 420, 420),
          scale: 2,
        },
      )

      const link = document.createElement('a')
      link.href = url
      link.download = `${fileNameFor(chart.title)}.png`
      document.body.appendChild(link)
      link.click()
      link.remove()
      setStatus('idle')
    } catch {
      // Export failed (canvas/tainted/unsupported) — surface it briefly
      // instead of failing silently, then return to the normal state.
      setStatus('failed')
      setTimeout(() => setStatus('idle'), 2600)
    }
  }

  if (!chart || chart.chart_type === 'none' || !chart.plotly_spec) return null

  const busy = status === 'working'

  return (
    <div className="overflow-hidden rounded-xl border border-white/8">
      <div className="flex items-center gap-2 border-b border-white/6 bg-white/[0.03] px-3.5 py-2">
        <BarChart3 className="h-3.5 w-3.5 shrink-0 text-brand-cyan" />
        <span className="truncate text-xs font-semibold uppercase tracking-wide text-slate-400">
          {chart.title || 'Visualization'}
        </span>

        <span className="ml-auto shrink-0 rounded-full border border-brand-violet/30 bg-brand-violet/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-violet">
          {TYPE_LABELS[chart.chart_type] || chart.chart_type}
        </span>
      </div>

      <div className="px-2 pb-2 pt-1.5">
        <ChartRenderer chart={chart} onGraphRef={handleGraphRef} isLight={isLight} />
      </div>

      {/* Footer action bar — the chart's own actions live with the chart, so
          it reads as downloadable at a glance. Only real actions appear. */}
      <div className="flex flex-wrap items-center gap-x-1 gap-y-1 border-t border-white/6 bg-white/[0.02] px-2.5 py-1.5">
        <button
          type="button"
          onClick={handleDownload}
          disabled={busy}
          className="action-button"
          aria-label="Download chart as a PNG image"
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" />
          ) : (
            <Download className="h-3.5 w-3.5 shrink-0" />
          )}
          {busy ? 'Preparing…' : 'Download chart'}
        </button>
        {status === 'failed' && (
          <span role="status" className="px-1.5 text-xs text-amber-300/90">
            Couldn&apos;t export — your browser may block image generation.
          </span>
        )}
      </div>
    </div>
  )
}
