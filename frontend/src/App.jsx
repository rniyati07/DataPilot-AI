import { useEffect, useState } from 'react'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import { applyTheme, getStoredTheme } from './lib/theme'

// Two views: a public landing page and the dashboard. State-based switching
// keeps the bundle dependency-free (no router needed for a single app flow).
// Theme lives here so both views share one preference.
export default function App() {
  const [view, setView] = useState('landing')
  const [theme, setTheme] = useState(() => getStoredTheme())

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  return view === 'landing' ? (
    <LandingPage onEnter={() => setView('dashboard')} theme={theme} onThemeChange={setTheme} />
  ) : (
    <DashboardPage
      onBackHome={() => setView('landing')}
      theme={theme}
      onThemeChange={setTheme}
    />
  )
}
