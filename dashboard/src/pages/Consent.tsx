import { AlertCircle, Copy, Printer } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Logo } from '../components/Logo'
import { ApiError, get, post } from '../lib/api'

type Notice = { child_id: number; child_name: string; text: string }
type ConsentState = {
  confirmed: boolean
  notice: Notice[]
  does_not_see: { title: string; text: string }[]
}

export function Consent({ onConfirmed, onLogout }: { onConfirmed: () => void; onLogout: () => void }) {
  const [state, setState] = useState<ConsentState | null>(null)
  const [tab, setTab] = useState(0)
  const [told, setTold] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    get<ConsentState>('/consent').then(setState).catch((e) => setError(e instanceof ApiError ? e.message : String(e)))
  }, [])

  const notice = state?.notice[tab]

  async function copy() {
    if (!notice) return
    try {
      await navigator.clipboard.writeText(notice.text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setError('Copying is blocked in this browser. Select the text and copy it instead.')
    }
  }

  async function confirm() {
    setBusy(true)
    setError(null)
    try {
      await post('/consent', { told_child: true })
      onConfirmed()
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e))
      setBusy(false)
    }
  }

  return (
    <div className="consent">
      <header className="consent-head">
        <div className="brand">
          <Logo />
          <span>HomeNet Guardian</span>
        </div>
        <button className="btn btn-ghost" onClick={onLogout}>Log out</button>
      </header>

      <main className="consent-main">
        <h1>Before you start: tell your children</h1>
        <p className="consent-lead">
          Nothing is installed on your children's devices, so they cannot see that the home network is monitored.
          That makes it your job to tell them. Here is a note you can read together, print or send.
        </p>

        <div className="panel consent-notice">
          {state && state.notice.length > 1 && (
            <div className="tabs" role="tablist" aria-label="Notice for">
              {state.notice.map((n, i) => (
                <button key={n.child_id} role="tab" aria-selected={tab === i} className="tab" onClick={() => setTab(i)}>
                  For {n.child_name}
                </button>
              ))}
            </div>
          )}
          <div className="notice-text">
            {notice ? notice.text.split('\n').map((line, i) => (line.trim() ? <p key={i}>{line}</p> : null))
              : <div className="skeleton" style={{ height: 180 }} />}
          </div>
          <div className="notice-actions">
            <button className="btn btn-secondary" onClick={copy} disabled={!notice}>
              <Copy /> {copied ? 'Copied' : 'Copy text'}
            </button>
            <button className="btn btn-secondary" onClick={() => window.print()} disabled={!notice}>
              <Printer /> Print
            </button>
          </div>
        </div>

        <div className="consent-confirm">
          <label className="check">
            <input type="checkbox" checked={told} onChange={(e) => setTold(e.target.checked)} />
            <span>I have told my children that the home Wi-Fi is monitored and what it can see.</span>
          </label>
          {error && (
            <div className="callout callout-error" role="alert">
              <AlertCircle /> <span>{error}</span>
            </div>
          )}
          <button className="btn btn-primary btn-lg" disabled={!told || busy} onClick={confirm}>
            {busy ? 'Saving…' : 'Confirm and open the dashboard'}
          </button>
        </div>
      </main>
    </div>
  )
}
