import {
  Database,
  Home,
  MessageSquare,
  MessageSquarePlus,
  Sparkles,
  Upload,
} from 'lucide-react'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import { MAX_VISIBLE_CONVERSATIONS } from '../lib/conversations'

// Sidebar: brand, New Chat, recent conversations, the session's active
// database, the tool capabilities, and the theme control. Recent chats are
// this browser's real past conversations (lib/conversations.js) — nothing here
// is placeholder content.
const TOOLS = ['get_schema', 'execute_query', 'generate_chart', 'explain_data', 'generate_flowchart']

export default function Sidebar({
  database,
  dbState,
  onNewChat,
  onBackHome,
  onUploadClick,
  conversations = [],
  activeConversationId,
  onSelectConversation,
  theme,
  onThemeChange,
}) {
  const recent = conversations.slice(0, MAX_VISIBLE_CONVERSATIONS)

  return (
    <aside className="hidden w-[268px] shrink-0 flex-col border-r border-white/5 bg-ink-900/40 backdrop-blur-xl md:flex">
      {/* Brand */}
      <div className="flex h-16 items-center border-b border-white/5 px-5">
        <Logo withWordmark />
      </div>

      {/* New chat */}
      <div className="p-4">
        <button
          type="button"
          onClick={onNewChat}
          className="focus-ring flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient px-4 py-2.5 text-sm font-semibold shadow-[0_4px_16px_rgb(99_102_241_/_0.35)] transition hover:opacity-90"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {/* Active database */}
      <div className="px-4">
        <div className="rounded-xl border border-white/8 bg-white/[0.03] p-3.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Active database
          </p>
          <div className="mt-2 flex items-center gap-2">
            <Database className="h-4 w-4 shrink-0 text-brand-cyan" />
            {dbState === 'ready' && database ? (
              <span className="truncate text-sm font-medium text-slate-200" title={database.name}>
                {database.name}
              </span>
            ) : dbState === 'loading' ? (
              <span className="text-sm text-slate-400">Checking…</span>
            ) : (
              <span className="text-sm text-amber-400">Backend unreachable</span>
            )}
          </div>
          <button
            type="button"
            onClick={onUploadClick}
            className="focus-ring mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-brand-cyan/40 hover:bg-white/10"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload database
          </button>
        </div>
      </div>

      <div className="mt-5 min-h-0 flex-1 overflow-y-auto px-4 pb-4">
        {/* Recent conversations — real, from this browser's history */}
        {recent.length > 0 && (
          <div className="mb-5">
            <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Recent chats
            </p>
            <ul className="mt-2 space-y-0.5">
              {recent.map((conversation) => {
                const active = conversation.id === activeConversationId
                return (
                  <li key={conversation.id}>
                    <button
                      type="button"
                      onClick={() => onSelectConversation?.(conversation.id)}
                      aria-current={active ? 'true' : undefined}
                      title={conversation.title}
                      className={`focus-ring flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-[13px] transition ${
                        active
                          ? 'bg-white/8 text-slate-100'
                          : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                      }`}
                    >
                      <MessageSquare
                        className={`h-3.5 w-3.5 shrink-0 ${active ? 'text-brand-cyan' : 'text-slate-600'}`}
                      />
                      <span className="truncate">{conversation.title}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>
        )}

        {/* Capabilities (static, truthful) */}
        <p className="px-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
          Agent tools
        </p>
        <ul className="mt-2 space-y-1">
          {TOOLS.map((tool) => (
            <li
              key={tool}
              className="flex items-center gap-2 rounded-lg px-2 py-1.5 font-mono text-xs text-slate-400"
            >
              <Sparkles className="h-3 w-3 text-brand-violet/70" />
              {tool}
            </li>
          ))}
        </ul>
        <p className="mt-4 px-1 text-[11px] leading-relaxed text-slate-600">
          Read-only analysis. QueryVista never modifies your database.
        </p>
      </div>

      {/* Theme + back to landing */}
      <div className="space-y-3 border-t border-white/5 p-4">
        <ThemeToggle theme={theme} onChange={onThemeChange} />
        <button
          type="button"
          onClick={onBackHome}
          className="focus-ring flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:bg-white/5 hover:text-slate-200"
        >
          <Home className="h-4 w-4" />
          Back to home
        </button>
      </div>
    </aside>
  )
}
