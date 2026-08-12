// DataPilot AI brand mark: a gradient tile with a pilot/compass glyph.
// `withWordmark` renders the full "DataPilot AI" lockup; otherwise the
// mark alone (avatar, sidebar icon, loading indicator).
export default function Logo({ withWordmark = false, size = 32, className = '' }) {
  const mark = (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-[10px] bg-brand-gradient shadow-[0_4px_16px_rgb(99_102_241_/_0.45)] ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" width={Math.round(size * 0.62)} height={Math.round(size * 0.62)} fill="none">
        <circle cx="12" cy="12" r="8.6" stroke="white" strokeWidth="1.7" opacity="0.95" />
        <path
          d="M12 12 L19 8 M12 12 L12 3.6 M12 12 L5 8"
          stroke="white"
          strokeWidth="1.7"
          strokeLinecap="round"
          opacity="0.95"
        />
        <circle cx="12" cy="12" r="1.7" fill="white" />
      </svg>
    </span>
  )

  if (!withWordmark) return mark

  return (
    <span className={`flex items-center gap-2.5 ${className}`}>
      {mark}
      <span className="flex flex-col leading-none">
        <span className="text-[15px] font-bold tracking-tight text-white">
          DataPilot <span className="text-gradient">AI</span>
        </span>
        <span className="mt-1 text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500">
          Data Analyst
        </span>
      </span>
    </span>
  )
}
