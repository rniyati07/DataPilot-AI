import { Sparkles } from 'lucide-react'
import FormattedMessage from '../lib/formatMessage'

// Insight/explanation section (frontend batch §Batch 4). Distinct visual
// treatment so the plain-language read on the result stands apart from the
// raw data above it. Renders only what the backend actually returned.
export default function ExplanationCard({ explanation }) {
  if (!explanation) return null

  return (
    <div className="rounded-xl border border-brand-violet/20 bg-gradient-to-br from-brand-violet/[0.08] to-brand-indigo/[0.05] px-4 py-3.5">
      <div className="flex items-center gap-2">
        <Sparkles className="h-3.5 w-3.5 text-brand-violet" />
        <span className="text-xs font-semibold uppercase tracking-wide text-brand-violet">
          AI Explanation
        </span>
      </div>
      <div className="mt-2.5 text-sm leading-relaxed text-slate-300">
        <FormattedMessage text={explanation} />
      </div>
    </div>
  )
}
