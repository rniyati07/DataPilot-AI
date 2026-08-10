// Real Plotly rendering (Phase 8). Uses the smaller dist-min bundle via the
// react-plotly.js factory; the backend's generate_chart tool already built the
// full plotly_spec, so this component is a thin renderer (Architecture Rule 9).
import createPlotlyComponent from 'react-plotly.js/factory'
import Plotly from 'plotly.js-dist-min'

const Plot = createPlotlyComponent(Plotly)

export default function ChartRenderer({ chart }) {
  if (!chart || chart.chart_type === 'none' || !chart.plotly_spec) return null

  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white p-2">
      <Plot
        data={chart.plotly_spec.data}
        layout={chart.plotly_spec.layout}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', minHeight: 320 }}
        useResizeHandler
      />
    </div>
  )
}
