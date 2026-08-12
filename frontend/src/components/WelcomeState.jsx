import { Sparkles } from 'lucide-react'
import Logo from './Logo'

// Starter questions grounded in what the backend can actually answer.
// When the built-in demo database is active, chips target its real tables;
// otherwise they stay database-agnostic.
const DEMO_CHIPS = [
  'Show top 5 products by revenue',
  'Show the monthly sales trend',
  'Show the database schema',
  'How does the query pipeline work?',
]

const GENERIC_CHIPS = [
  'Show me the database schema',
  'How many rows are in each table?',
  'What can you tell me about my data?',
  'How does the query pipeline work?',
]

export default function WelcomeState({ database, dbState, onAsk, isLoading }) {
  const chips = database?.source === 'upload' ? GENERIC_CHIPS : DEMO_CHIPS

  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col items-center justify-center px-5 py-10 text-center">
      <div className="animate-fade-up">
        <div className="mx-auto w-fit">
          <Logo size={56} />
        </div>

        <h2 className="mt-6 text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Hi, I&apos;m <span className="text-gradient">DataPilot</span>.
        </h2>

        <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-400 sm:text-base">
          I&apos;m connected to your active database
          {dbState === 'ready' && database ? (
            <>
              {' '}
              — <span className="font-medium text-slate-200">{database.name}</span>
            </>
          ) : null}
          . Ask me anything about your data in plain English and I&apos;ll query
          it, visualize it, and explain what I find.
        </p>
      </div>

      <div className="mt-9 grid w-full grid-cols-1 gap-2.5 sm:grid-cols-2">
        {chips.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => onAsk(chip)}
            disabled={isLoading}
            className="group glass-card flex items-center justify-between gap-3 rounded-xl px-4 py-3 text-left text-sm text-slate-300 transition hover:border-brand-indigo/40 hover:bg-white/[0.06] disabled:opacity-50"
          >
            <span className="leading-snug">{chip}</span>
            <Sparkles className="h-4 w-4 shrink-0 text-brand-violet/60 transition group-hover:text-brand-cyan" />
          </button>
        ))}
      </div>

      <p className="mt-6 text-xs text-slate-600">
        Questions run through the real analysis pipeline — schema discovery,
        read-only SQL, charts, and explanations.
      </p>
    </div>
  )
}
