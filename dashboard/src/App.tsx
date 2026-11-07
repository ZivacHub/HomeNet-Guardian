import { useCallback, useEffect, useState } from 'react'
import { TopBar } from './components/TopBar'
import { ApiError, get, onAuthProblem, post, type Parent } from './lib/api'
import { useRoute, type RouteId } from './lib/routes'
import { applyTheme, loadTheme, type Theme } from './lib/theme'
import { Consent } from './pages/Consent'
import { InProgress } from './pages/InProgress'
import { Login } from './pages/Login'

type Phase = 'loading' | 'offline' | 'login' | 'consent' | 'app'

const SCREENS: Record<RouteId, { title: string; step: string; what: string }> = {
  overview: { title: 'Overview', step: '3.2', what: 'Who is online, today per child, and warnings that need you.' },
  devices: { title: 'Devices', step: '3.3', what: 'Every device on the home Wi-Fi, and whose it is.' },
  activity: { title: 'Live activity', step: '3.4', what: 'Each site a device asks for, as it happens.' },
  time: { title: 'Where time goes', step: '3.5', what: 'An estimate of time per category and site, for each child.' },
  rules: { title: 'Rules', step: '3.6', what: 'Blocked categories, bedtimes and the pause button.' },
  payments: { title: 'Payments & stores', step: '3.7', what: 'Store and payment sites wait for your OK.' },
  reports: { title: 'Reports', step: '4.2', what: 'Weekly and monthly summaries.' },
  settings: { title: 'Settings', step: '3.8', what: 'Records, parents, the family notice, and what this does not see.' },
}

export default function App() {
  const [phase, setPhase] = useState<Phase>('loading')
  const [parent, setParent] = useState<Parent | null>(null)
  const [theme, setTheme] = useState<Theme>(loadTheme)
  const route = useRoute()

  useEffect(() => applyTheme(theme), [theme])

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

  return (
    <>
      <TopBar route={route} parent={parent!} theme={theme} onTheme={setTheme} onLogout={logout} />
      <main id="main">
        <InProgress {...SCREENS[route]} />
      </main>
    </>
  )
}
