// Theme control (refinement Part B). Dark is DataPilot's identity and stays
// the default; light is a professional equivalent, not an inversion.
//
// The switch works by putting `data-theme` on <html>. index.css redefines the
// surface/text tokens under that attribute, so every existing component adapts
// without touching its markup. Components that draw to a canvas or SVG
// (Plotly, Mermaid) can't read CSS tokens, so they receive an `isLight` prop.
const STORAGE_KEY = 'datapilot_theme'

export const THEMES = ['dark', 'light']

export function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (THEMES.includes(stored)) return stored
  } catch {
    // localStorage unavailable (private mode) — fall through to the default.
  }
  return 'dark'
}

export function applyTheme(theme) {
  const resolved = THEMES.includes(theme) ? theme : 'dark'
  document.documentElement.setAttribute('data-theme', resolved)
  // Keeps native form controls and scrollbars in step with the theme.
  document.documentElement.style.colorScheme = resolved
  try {
    localStorage.setItem(STORAGE_KEY, resolved)
  } catch {
    // Preference simply won't persist; the app still works.
  }
  return resolved
}
