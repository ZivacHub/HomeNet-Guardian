import { AlertCircle, Info } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Logo } from '../components/Logo'
import { ApiError, post, type Parent } from '../lib/api'

export function Login({ onLoggedIn }: { onLoggedIn: (p: Parent) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const r = await post<{ parent: Parent }>('/auth/login', { username, password })
      onLoggedIn(r.parent)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'The server could not be reached. Is it running?')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth">
      <section className="auth-story">
        <div className="brand brand-lg">
          <Logo size={36} />
          <span>HomeNet Guardian</span>
        </div>
        <h1 className="auth-title">See what happens on your home Wi-Fi, without installing anything on your child's phone.</h1>
        <ul className="auth-points">
          <li>Which sites each device asks for, and when</li>
          <li>Explicit sites blocked for every device</li>
          <li>Store and payment sites wait for a parent's OK</li>
          <li>Bedtimes, pauses and a weekly picture of where time goes</li>
        </ul>
        <p className="auth-foot muted">
          Runs only on this computer. This demo uses a simulated family network: Mom, Dad, Ana (14) and Luka (9).
        </p>
      </section>

      <section className="auth-card panel">
        <form onSubmit={submit} className="auth-form" noValidate>
          <h2>Log in</h2>
          <div className="field">
            <label htmlFor="u">Username</label>
            <input id="u" className="input" autoComplete="username" value={username}
              onChange={(e) => setUsername(e.target.value)} aria-invalid={!!error} autoFocus />
          </div>
          <div className="field">
            <label htmlFor="p">Password</label>
            <input id="p" className="input" type="password" autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)} aria-invalid={!!error} />
          </div>
          {error && (
            <div className="callout callout-error" role="alert">
              <AlertCircle />
              <span>{error}</span>
            </div>
          )}
          <button className="btn btn-primary btn-lg" disabled={busy || !username || !password}>
            {busy ? 'Logging in…' : 'Log in'}
          </button>
          <div className="callout callout-info">
            <Info />
            <span>
              Demo login: <strong className="mono">demo</strong> / <strong className="mono">demo</strong> (Mom),
              or <strong className="mono">dad</strong> / <strong className="mono">demo</strong>.
            </span>
          </div>
        </form>
      </section>
    </div>
  )
}
