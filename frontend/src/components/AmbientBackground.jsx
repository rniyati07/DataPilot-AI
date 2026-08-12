// Ambient dark-navy backdrop shared by the landing page and dashboard:
// deep base color, subtle grid, and three restrained radial glows
// (blue / violet / cyan) that never compete with content.
export default function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-ink-950">
      <div className="bg-grid absolute inset-0" />

      {/* Blue ambient glow — top-left */}
      <div
        className="absolute -left-40 -top-48 h-[36rem] w-[36rem] rounded-full bg-brand-indigo/25 blur-[110px]"
        aria-hidden="true"
      />
      {/* Violet ambient glow — top-right */}
      <div
        className="absolute -right-48 -top-40 h-[40rem] w-[40rem] rounded-full bg-brand-violet/20 blur-[120px]"
        aria-hidden="true"
      />
      {/* Cyan ambient glow — bottom */}
      <div
        className="absolute -bottom-56 left-1/2 h-[34rem] w-[46rem] -translate-x-1/2 rounded-full bg-brand-cyan/10 blur-[130px]"
        aria-hidden="true"
      />

      {/* Vignette so edges settle into the base color */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,rgb(7_11_22_/_0.7)_100%)]" />
    </div>
  )
}
