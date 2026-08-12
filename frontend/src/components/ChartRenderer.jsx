// Real Plotly rendering (Phase 8). Uses the smaller dist-min bundle via the
// react-plotly.js factory; the backend's generate_chart tool already built the
// full plotly_spec, so this component is a thin renderer (Architecture Rule 9).
//
// Theming is presentation-only: the backend owns chart_type and the data, and
// this file never changes either. It adapts colours for the active theme and
// gives the plot a deterministic size.
import { useMemo, useState } from 'react'
import createPlotlyComponent from 'react-plotly.js/factory'
import Plotly from 'plotly.js-dist-min'

const Plot = createPlotlyComponent(Plotly)

// Cartesian traces get themed axes; pie has none, so injecting axis keys into
// its layout is both pointless and a source of render errors.
const CARTESIAN_TYPES = new Set(['bar', 'line', 'scatter'])
const PLOT_HEIGHT = 340
const PIE_PLOT_HEIGHT = 380

function palette(isLight) {
  return isLight
    ? {
        grid: 'rgba(71, 85, 105, 0.16)',
        zero: 'rgba(71, 85, 105, 0.3)',
        tick: '#475569',
        text: '#0f172a',
        title: '#0f172a',
      }
    : {
        grid: 'rgba(148, 163, 184, 0.12)',
        zero: 'rgba(148, 163, 184, 0.25)',
        tick: '#94a3b8',
        text: '#cbd5e1',
        title: '#f1f5f9',
      }
}

// Plotly v3 wants `title: { text }`; the backend sends a plain string.
function axisTitle(title, color) {
  if (title === undefined || title === null) return undefined
  const text = typeof title === 'string' ? title : title.text
  return { text, font: { color, size: 12 } }
}

function themeAxis(axis, colors) {
  const base = axis || {}
  return {
    ...base,
    title: axisTitle(base.title, colors.tick),
    gridcolor: colors.grid,
    zerolinecolor: colors.zero,
    linecolor: colors.grid,
    tickfont: { ...(base.tickfont || {}), color: colors.tick, size: 11 },
  }
}

function buildLayout(spec, chartType, isLight) {
  const base = spec?.layout || {}
  const colors = palette(isLight)
  const isCartesian = CARTESIAN_TYPES.has(chartType)

  // Copy the backend layout, then drop keys we are about to re-derive so no
  // stale or undefined axis entries survive into a pie layout.
  const layout = { ...base }
  delete layout.xaxis
  delete layout.yaxis

  layout.paper_bgcolor = 'rgba(0,0,0,0)'
  layout.plot_bgcolor = 'rgba(0,0,0,0)'
  layout.font = {
    ...(base.font || {}),
    color: colors.text,
    family: 'Inter, ui-sans-serif, system-ui, sans-serif',
    size: 12,
  }
  // An explicit height keeps sizing deterministic instead of depending on the
  // container resolving a CSS min-height before Plotly measures it.
  layout.height = chartType === 'pie' ? PIE_PLOT_HEIGHT : PLOT_HEIGHT
  layout.autosize = true
  layout.margin = base.margin || { l: 56, r: 24, t: 48, b: 44 }

  if (base.title) {
    const text = typeof base.title === 'string' ? base.title : base.title.text
    layout.title = { text, font: { color: colors.title, size: 13 }, x: 0.5, xanchor: 'center' }
  }

  if (base.showlegend) {
    layout.showlegend = true
    layout.legend = {
      ...(base.legend || {}),
      font: { color: colors.text, size: 11 },
      bgcolor: 'rgba(0,0,0,0)',
    }
  }

  if (isCartesian) {
    layout.xaxis = themeAxis(base.xaxis, colors)
    layout.yaxis = themeAxis(base.yaxis, colors)
  }

  return layout
}

export default function ChartRenderer({ chart, onGraphRef, isLight = false }) {
  const [failed, setFailed] = useState(false)

  const chartType = chart?.chart_type
  const layout = useMemo(
    () => buildLayout(chart?.plotly_spec, chartType, isLight),
    [chart, chartType, isLight],
  )

  if (!chart || chartType === 'none' || !chart.plotly_spec) return null

  const traces = chart.plotly_spec.data
  // A malformed or empty trace list would otherwise render an empty plot box.
  if (!Array.isArray(traces) || traces.length === 0) {
    return (
      <p role="status" className="px-3 py-8 text-center text-sm text-slate-400">
        This result did not include chart data to render.
      </p>
    )
  }

  if (failed) {
    return (
      <p role="status" className="px-3 py-8 text-center text-sm text-amber-300/90">
        This chart could not be rendered. The result table above still shows the data.
      </p>
    )
  }

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%' }}
      useResizeHandler
      onInitialized={(figure, graphDiv) => onGraphRef?.(graphDiv)}
      onUpdate={(figure, graphDiv) => onGraphRef?.(graphDiv)}
      onPurge={() => onGraphRef?.(null)}
      // Without this, a Plotly exception leaves a silently blank card.
      onError={() => setFailed(true)}
    />
  )
}
