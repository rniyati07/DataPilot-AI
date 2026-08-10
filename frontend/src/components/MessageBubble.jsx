import SqlPanel from './SqlPanel'
import ResultTable from './ResultTable'
import ChartRenderer from './ChartRenderer'
import DiagramRenderer from './DiagramRenderer'

export default function MessageBubble({ role, content }) {
  const isUser = role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-slate-900 px-4 py-2 text-white">
          {content.message}
        </div>
      </div>
    )
  }

  // Agent turn: SQL -> Result table -> Chart/Diagram -> Explanation (PRD §5.6 order).
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-3 rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3">
        <p className="text-slate-800">{content.message}</p>
        <SqlPanel sql={content.sql} />
        <ResultTable columns={content.columns} rows={content.rows} />
        <ChartRenderer chart={content.chart} />
        <DiagramRenderer diagram={content.diagram} />
        {content.explanation && <p className="text-sm text-slate-600">{content.explanation}</p>}
      </div>
    </div>
  )
}
