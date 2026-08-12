import { Moon, Sun } from 'lucide-react'

// Compact theme control (refinement Part B). Two explicit states rather than a
// cycling button, so the current theme is always legible at a glance.
export default function ThemeToggle({ theme, onChange }) {
  return (
    <div
      className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] p-1"
      role="group"
      aria-label="Colour theme"
    >
      {[
        { value: 'dark', label: 'Dark', Icon: Moon },
        { value: 'light', label: 'Light', Icon: Sun },
      ].map(({ value, label, Icon }) => {
        const active = theme === value
        return (
          <button
            key={value}
            type="button"
            onClick={() => onChange(value)}
            aria-pressed={active}
            className={`focus-ring flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium transition ${
              active
                ? 'bg-white/10 text-slate-100 shadow-sm'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        )
      })}
    </div>
  )
}
