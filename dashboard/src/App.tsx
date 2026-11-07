import { useCallback, useEffect, useState } from 'react'
import { TopBar } from './components/TopBar'
import { ApiError, get, onAuthProblem, post, type Parent } from './lib/api'
import { useRoute, type RouteId } from './lib/routes'
import { applyTheme, loadTheme, type Theme } from './lib/theme'
import { Consent } from './pages/Consent'
import { InProgress } from './pages/InProgress'
import Activity from './pages/Activity'
import Devices from './pages/Devices'
import Overview from './pages/Overview'
import Payments from './pages/Payments'
import Rules from './pages/Rules'
import { SCREEN_INFO } from './pages/screenInfo'
import Settings from './pages/Settings'
import Time from './pages/Time'
import { Login } from './pages/Login'

type Phase = 'loading' | 'offline' | 'login' | 'consent' | 'app'

// One file per screen (pages/*.tsx). Reports arrives in Phase 4.
const PAGES: Record<RouteId, () => React.JSX.Element> = {
  overview: Overview,
  devices: Devices,
  activity: Activity,
  time: Time,
  rules: Rules,
  payments: Payments,
  reports: () => <InProgress {...SCREEN_INFO.reports} />,
  settings: Settings,
}

export default function App() {
  const [phase, setPhase] = useState<Phase>('loading')
  const [parent, setParent] = useState<Parent | null>(null)
  const [theme, setTheme] = useState<Theme>(loadTheme)
  const route = useRoute()

  useEffect(() => applyTheme(theme), [theme])

  useEffect(() => {
    const t = phase === 'app' ? SCREEN_INFO[route].title : phase === 'consent' ? 'Before you start' : 'Log in'
    document.title = `${t} · HomeNet Guardian`
  }, [phase, route])

  const check = useCallback(async () => {
    try {
      const me = await get<{ parent: Parent }>('/auth/me')
      setParent(me.parent)
      const c = await get<{ confirmed: boolean }>('/consent')
      setPhase(c.confirmed ? 'app' : 'consent')
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) setPhase('login')
      else setPhase('offline')
    }
  }, [])

  useEffect(() => {
    check()
  }, [check])

  useEffect(
    () =>
      onAuthProblem((e) => {
        if (e.status === 401) setPhase('login')
        else if (e.code === 'consent_required') setPhase('consent')
      }),
    [],
  )

  async function logout() {
    try {
      await post('/auth/logout')
    } finally {
      setParent(null)
      setPhase('login')
    }
  }

  if (phase === 'loading') return <div className="boot" aria-busy="true" />
  if (phase === 'offline')
    return (
      <div className="page">
        <div className="panel empty">
          <h2>The HomeNet Guardian server is not answering</h2>
          <p>Start it with <span className="mono">npm run dev</span> in the project folder, then reload this page.</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={check}>Try again</button>
        </div>
      </div>
    )
  if (phase === 'login') return <Login onLoggedIn={(p) => { setParent(p); check() }} />
  if (phase === 'consent') return <Consent onConfirmed={() => setPhase('app')} onLogout={logout} />

  const Page = PAGES[route]
  return (
    <>
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); document.getElementById('main')?.focus() }}>
        Skip to content
      </a>
      <TopBar route={route} parent={parent!} theme={theme} onTheme={setTheme} onLogout={logout} />
      <main id="main" tabIndex={-1}>
        <Page key={route} />
      </main>
    </>
  )
}
