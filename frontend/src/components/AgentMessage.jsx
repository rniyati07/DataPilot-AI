import Logo from './Logo'
import SqlPanel from './SqlPanel'
import ResultTable from './ResultTable'
import ChartCard from './ChartCard'
import DiagramCard from './DiagramCard'
import ExplanationCard from './ExplanationCard'
import FormattedMessage from '../lib/formatMessage'

// The agent's turn, composed in the PRD §5.6 order:
//   answer → Generated SQL → Result table → Chart → Diagram → Explanation.
// Each section renders only when the real API response provides it; nothing
// is invented or forced. Structured agent errors arrive inside the envelope
// (HTTP 200) and get an error-styled answer instead of a data card stack.
export default function AgentMessage({ content, isLight }) {
  const hasError = Boolean(content?.error)
  const hasResult = !hasError && content?.columns?.length > 0

  return (
    <div className="flex items-start gap-3">
      <Logo size={30} className="mt-1" />
      <div className="min-w-0 flex-1">
        <p className="mb-1.5 text-xs font-semibold text-slate-400">DataPilot</p>
        <div className="space-y-3">
          {hasError ? (
            <div className="animate-fade-in rounded-2xl rounded-bl-sm border border-red-400/25 bg-red-400/[0.08] px-4 py-3.5 text-sm leading-relaxed text-red-200">
              <FormattedMessage text={content.message} />
            </div>
          ) : (
            <div className="glass-card animate-fade-up rounded-2xl rounded-bl-sm px-4 py-3.5">
              <div className="text-sm leading-relaxed text-slate-200">
                <FormattedMessage text={content.message} />
              </div>
            </div>
          )}

          <SqlPanel sql={content.sql} hasError={hasError} />
          {hasResult && <ResultTable columns={content.columns} rows={content.rows} />}
          <ChartCard chart={content.chart} isLight={isLight} />
          <DiagramCard diagram={content.diagram} isLight={isLight} />
          <ExplanationCard explanation={content.explanation} />
        </div>
      </div>
    </div>
  )
}
