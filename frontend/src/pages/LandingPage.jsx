import {
  ArrowRight,
  BarChart3,
  Code2,
  Database,
  FileSearch,
  MessageCircle,
  Network,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import AmbientBackground from '../components/AmbientBackground'
import Logo from '../components/Logo'

// Truthful capability statements — the actual implementation, not invented
// performance numbers (frontend batch prompt §Batch 1.5).
const CAPABILITIES = [
  {
    icon: Sparkles,
    title: '5 AI tools',
    subtitle: 'schema · query · chart · explain · diagram',
  },
  {
    icon: ShieldCheck,
    title: 'Read-only SQL execution',
    subtitle: 'writes are rejected by design',
  },
  {
    icon: Database,
    title: 'Live schema grounding',
    subtitle: 'tables & columns discovered from your database',
  },
]

const FEATURES = [
  {
    icon: MessageCircle,
    title: 'Natural Language Queries',
    description:
      'Ask questions about your database in plain English. DataPilot interprets intent and routes it through a real analysis pipeline — not a keyword search.',
  },
  {
    icon: Code2,
    title: 'Smart SQL Generation',
    description:
      'Every question becomes accurate, read-only SQL. Table and column names come from your database’s live schema — nothing is guessed or invented.',
  },
  {
    icon: BarChart3,
    title: 'Real-time Visualization',
    description:
      'Query results become interactive Plotly charts — bars, lines, pies, and scatter. The chart type is chosen from the result’s shape, not by guesswork.',
  },
  {
    icon: Network,
    title: 'ER & Process Diagrams',
    description:
      'Visualize your database schema as an entity-relationship diagram, or render step-by-step process flows — assembled as Mermaid diagrams on demand.',
  },
  {
    icon: Sparkles,
    title: 'Insightful Explanations',
    description:
      'Every result is summarized in clear, plain language — grounded strictly in the rows actually returned, with nothing extrapolated.',
  },
  {
    icon: FileSearch,
    title: 'Transparent Results',
    description:
      'You always see the generated SQL and the raw rows behind an answer. Nothing is hidden — the reasoning behind each result is fully auditable.',
  },
]

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Ask your data',
    description:
      'Type a question in plain English — "show me the top products by revenue" — and DataPilot starts a real analysis turn against your active database.',
  },
  {
    step: '02',
    title: 'DataPilot analyzes',
    description:
      'The agent inspects your live schema, writes safe read-only SQL, executes it, and builds charts and explanations from the actual result rows.',
  },
  {
    step: '03',
    title: 'Understand the result',
    description:
      'Review the generated SQL, the returned rows, charts, and a plain-language explanation — all grounded in your data, in one conversation.',
  },
]

const NAV_LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#demo', label: 'Demo' },
]

// Real questions the bundled demo database can answer — the same kinds of
// prompts the dashboard suggests. Nothing here implies a capability the agent
// does not have.
const DEMO_QUESTIONS = [
  'Show me the top 5 products by revenue.',
  'Show the monthly revenue trend as a line chart.',
  'Show revenue share by category as a pie chart.',
  'Show me the database schema.',
  'How does an order move through the system?',
  'How many customers are in the database?',
]

export default function LandingPage({ onEnter }) {
  return (
    <div className="relative min-h-screen text-slate-200">
      <AmbientBackground />

      {/* ---------- Nav ----------
          Section links only. The hero already carries the primary CTA, so a
          second "Enter Dashboard" up here would just duplicate it. */}
      <header className="sticky top-0 z-20 border-b border-white/5 bg-ink-950/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5">
          <Logo withWordmark />
          <nav aria-label="Sections">
            <ul className="flex items-center gap-1 sm:gap-2">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="focus-ring inline-block rounded-lg px-3 py-2 text-sm font-medium text-slate-400 transition hover:bg-white/5 hover:text-slate-100"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      {/* ---------- Hero ---------- */}
      <section className="relative">
        <div className="mx-auto max-w-6xl px-5 pb-24 pt-20 text-center sm:pt-28">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-cyan/30 bg-brand-cyan/10 px-4 py-1.5 text-xs font-medium text-brand-cyan">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-cyan opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-cyan" />
            </span>
            AI-powered data analysis · connected to your database
          </span>

          <h1 className="mx-auto mt-8 max-w-3xl text-4xl font-extrabold leading-[1.08] tracking-tight text-white sm:text-6xl">
            Talk to Your Data.
            <br />
            <span className="text-gradient">Get Answers.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-slate-400 sm:text-lg">
            DataPilot AI is a conversational data analyst. Interact with your
            database using natural language — it generates SQL, runs it
            read-only, and turns the results into charts, diagrams, and
            plain-language insights.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <button
              type="button"
              onClick={onEnter}
              className="group inline-flex items-center gap-2 rounded-xl bg-brand-gradient px-7 py-3.5 text-base font-semibold text-white shadow-[0_8px_28px_rgb(99_102_241_/_0.45)] transition hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan"
            >
              Enter Dashboard
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5" />
            </button>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-3.5 text-base font-semibold text-slate-200 transition hover:border-white/20 hover:bg-white/10"
            >
              Explore features
            </a>
          </div>

          {/* Capability trio — replaces unsupported metrics */}
          <div className="mx-auto mt-16 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
            {CAPABILITIES.map((cap) => (
              <div
                key={cap.title}
                className="glass-card flex items-start gap-3 rounded-2xl p-4 text-left"
              >
                <cap.icon className="mt-0.5 h-5 w-5 shrink-0 text-brand-cyan" />
                <div>
                  <p className="text-sm font-semibold text-white">{cap.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-400">
                    {cap.subtitle}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Features ---------- */}
      <section id="features" className="relative scroll-mt-16 border-t border-white/5 py-24">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Everything you need to understand your data
            </h2>
            <p className="mt-4 text-slate-400">
              Six focused capabilities, each grounded in the real agent
              pipeline — from schema discovery to transparent results.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="glass-card glass-card-hover rounded-2xl p-6"
              >
                <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-indigo/15 ring-1 ring-brand-indigo/25">
                  <feature.icon className="h-5 w-5 text-brand-cyan" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- How it works ---------- */}
      <section id="how-it-works" className="relative scroll-mt-16 border-t border-white/5 py-24">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              How it works
            </h2>
            <p className="mt-4 text-slate-400">
              A question in, a grounded answer out — in three steps.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-5 md:grid-cols-3">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step} className="glass-card rounded-2xl p-6">
                <span className="bg-gradient-to-br from-brand-cyan to-brand-violet bg-clip-text text-4xl font-extrabold text-transparent">
                  {item.step}
                </span>
                <h3 className="mt-3 text-lg font-semibold text-white">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Demo ----------
          Points at what the bundled database can genuinely answer, rather than
          showing a mocked-up conversation with invented figures. */}
      <section id="demo" className="relative scroll-mt-16 border-t border-white/5 py-24">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Try it on the demo database
            </h2>
            <p className="mt-4 text-slate-400">
              DataPilot ships with a small e-commerce SQLite database — customers,
              categories, products, orders, order items, inventory and payments.
              Open the dashboard and ask any of these, or upload your own SQLite
              file and ask about that instead.
            </p>
          </div>

          <ul className="mx-auto mt-12 grid max-w-4xl grid-cols-1 gap-3 sm:grid-cols-2">
            {DEMO_QUESTIONS.map((question) => (
              <li
                key={question}
                className="glass-card flex items-start gap-3 rounded-xl px-4 py-3 text-left text-sm text-slate-300"
              >
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-brand-violet" />
                {question}
              </li>
            ))}
          </ul>

          <div className="mt-12 flex justify-center">
            <button
              type="button"
              onClick={onEnter}
              className="focus-ring group inline-flex items-center gap-2 rounded-xl bg-brand-gradient px-7 py-3.5 text-base font-semibold shadow-[0_8px_28px_rgb(99_102_241_/_0.45)] transition hover:opacity-90"
            >
              Enter Dashboard
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5" />
            </button>
          </div>
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="border-t border-white/5 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-5 sm:flex-row">
          <Logo withWordmark />
          <p className="text-xs text-slate-500">
            Conversational AI data analyst · read-only SQL · live schema grounding
          </p>
        </div>
      </footer>
    </div>
  )
}
