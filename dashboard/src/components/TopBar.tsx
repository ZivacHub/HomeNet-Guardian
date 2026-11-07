import { LogOut, Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'
import { get, type Parent } from '../lib/api'
import { href, ROUTES, type RouteId } from '../lib/routes'
import type { Theme } from '../lib/theme'
import { Logo } from './Logo'

type Props = {
  route: RouteId
  parent: Parent
  theme: Theme
  onTheme: (t: Theme) => void
  onLogout: () => void
}

/** The simulated time from the server (it follows the PC clock, or a set clock in a picture run). */
function useClock() {
  const [now, setNow] = useState<Date | null>(null)
  useEffect(() => {
    let alive = true
    const load = () =>
      get<{ now: string }>('/clock')
        .then((r) => alive && setNow(new Date(r.now)))
        .catch(() => {})
    load()
    const t = window.setInterval(load, 15_000)
    return () => {
      alive = false
      window.clearInterval(t)
    }
  }, [])
  return now
}

function usePendingApprovals(): number {
  const [n, setN] = useState(0)
  useEffect(() => {
    let alive = true
    const load = () =>
      get<{ items: unknown[] }>('/approvals?status=pending')
        .then((r) => alive && setN(r.items.length))
        .catch(() => {})
    load()
    const t = window.setInterval(load, 10_000)
    window.addEventListener('hg:approvals-changed', load)   // Payments answered a request
    return () => {
      alive = false
      window.clearInterval(t)
      window.removeEventListener('hg:approvals-changed', load)
    }
  }, [])
  return n
}

export function TopBar({ route, parent, theme, onTheme, onLogout }: Props) {
  const now = useClock()
  const pending = usePendingApprovals()
  const day = now ? now.toLocaleDateString('en-GB', { weekday: 'short' }) : ''
  const time = now ? now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : ''

  return (
    <header className="topbar">
      <div className="topbar-row">
        <a className="brand" href={href('overview')}>
          <Logo />
          <span>HomeNet Guardian</span>
        </a>

        <nav className="nav" aria-label="Main">
          {ROUTES.map((r) => (
            <a key={r.id} href={href(r.id)} className="nav-link" aria-current={route === r.id ? 'page' : undefined}>
              {r.label}
              {r.id === 'payments' && pending > 0 && (
                <span className="nav-count" aria-label={`${pending} waiting`}>{pending}</span>
              )}
            </a>
          ))}
        </nav>

        <div className="topbar-tools">
          <span className="sim-pill" title="All devices and lookups are simulated. No real network is monitored.">
            <span className="sim-dot" aria-hidden="true" />
            Simulated network · <span className="num">{day} {time}</span>
          </span>
          <button
            className="btn btn-ghost btn-icon"
            onClick={() => onTheme(theme === 'light' ? 'dark' : 'light')}
            aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
            title={theme === 'light' ? 'Dark theme' : 'Light theme'}
          >
            {theme === 'light' ? <Moon /> : <Sun />}
          </button>
          <span className="who">{parent.display_name}</span>
          <button className="btn btn-ghost btn-icon" onClick={onLogout} aria-label="Log out" title="Log out">
            <LogOut />
          </button>
        </div>
      </div>
    </header>
  )
}
