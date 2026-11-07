import {
  AlertCircle, Clock, Copy, Eye, EyeOff, KeyRound, Lock, MessageSquareOff, Printer, RefreshCw, Shield,
  Shuffle, SignalHigh, Trash2, UserPlus,
} from 'lucide-react'
import type { ComponentType, FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { ApiError, patch, post } from '../lib/api'
import { clock } from '../lib/format'
import { usePoll } from '../lib/usePoll'
import { SCREEN_INFO } from './screenInfo'
import '../styles/pages/settings.css'

type SettingsData = { retention_days: number; approval_minutes_default: number }
type Summary = {
  counts: { queries: number; alerts: number; approval_requests: number; pauses: number }
  oldest_record: string | null
  retention_days: number
}
type ConsentData = {
  confirmed: boolean
  confirmed_by: string | null
  confirmed_at: string | null
  notice: { child_id: number; child_name: string; text: string }[]
  does_not_see: { title: string; text: string }[]
}
type ParentRow = { id: number; username: string; display_name: string }
type ParentsData = { parents: ParentRow[]; max: number }
type Meta = { today: string }
type SettingsPoll = ReturnType<typeof usePoll<SettingsData>>
type ConsentPoll = ReturnType<typeof usePoll<ConsentData>>
type SaveState = 'idle' | 'saving' | 'saved' | 'error'

const RETENTION_CHOICES = [7, 14, 30, 60, 90]
const APPROVAL_CHOICES = [15, 30, 60, 120]

const SECTIONS = [
  { id: 'does-not-see', label: 'What this does not see' },
  { id: 'records', label: 'Records' },
  { id: 'approvals', label: 'Payment approvals' },
  { id: 'family-notice', label: 'Family notice' },
  { id: 'parents', label: 'Parents' },
]

const ICONS: Record<string, ComponentType> = {
  'Messages and page content': MessageSquareOff,
  'Mobile data': SignalHigh,
  VPNs: Shield,
  'Encrypted DNS': Lock,
  'Encrypted site names': KeyRound,
  'Devices that change': Shuffle,
  'Time spent': Clock,
}
function iconFor(title: string): ComponentType {
  const key = Object.keys(ICONS).find((k) => title.startsWith(k))
  return key ? ICONS[key] : EyeOff
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
function dayLabel(ts: string): string {
  return `${Number(ts.slice(8, 10))} ${MONTHS[Number(ts.slice(5, 7)) - 1]} ${ts.slice(0, 4)}`
}
const num = (v: number) => v.toLocaleString('en-US')
const errText = (e: unknown) => (e instanceof ApiError ? e.message : 'The server could not be reached.')

function Failed({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="panel-pad">
      <div className="callout callout-error" role="alert">
        <AlertCircle /> <span>{message}</span>
      </div>
      <button className="btn btn-secondary set-retry" onClick={onRetry}><RefreshCw /> Try again</button>
    </div>
  )
}

function Loading({ rows = 2 }: { rows?: number }) {
  return (
    <div className="panel-pad set-skeletons" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => <div key={i} className="skeleton" style={{ height: 22 }} />)}
    </div>
  )
}

function SaveNote({ state, msg }: { state: SaveState; msg: string }) {
  return (
    <span className="set-note" data-kind={state === 'error' ? 'error' : undefined} aria-live="polite">
      {state === 'saving' ? 'Saving…' : state === 'saved' ? 'Saved' : state === 'error' ? msg : ''}
    </span>
  )
}

/* ---- 1. What this does not see ---- */
function DoesNotSee({ consent }: { consent: ConsentPoll }) {
  const { data, error, loading, reload } = consent
  return (
    <section className="panel set-section" id="does-not-see" aria-labelledby="h-does-not-see">
      <div className="panel-head"><h2 id="h-does-not-see">What this does not see</h2></div>
      <div className="panel-pad set-intro">
        <p>HomeNet Guardian only sees site names and times on your home Wi-Fi. Here is what it cannot see.</p>
      </div>
      {loading && !data ? <Loading rows={4} /> : error && !data ? <Failed message={error} onRetry={reload} /> : (
        <ul className="set-limits">
          {data?.does_not_see.map((item) => {
            const Icon = iconFor(item.title)
            return (
              <li key={item.title}>
                <span className="set-limit-icon" aria-hidden="true"><Icon /></span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </div>
              </li>
            )
          })}
        </ul>
      )}
      <div className="panel-pad set-router">
        <p>On a real OpenWrt router these facts are the same: the router sees lookups and connection names, not content.</p>
      </div>
    </section>
  )
}

/* ---- 2. Records ---- */
function Records({ settings }: { settings: SettingsPoll }) {
  const summary = usePoll<Summary>('/data/summary', 15000)
  const meta = usePoll<Meta>('/meta', 0)
  const [days, setDays] = useState<number | null>(null)
  const [state, setState] = useState<SaveState>('idle')
  const [msg, setMsg] = useState('')
  const [confirmText, setConfirmText] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [delError, setDelError] = useState<string | null>(null)
  const [deleted, setDeleted] = useState<Summary['counts'] | null>(null)

  const current = days ?? settings.data?.retention_days ?? null

  async function save(value: number) {
    setDays(value)
    setState('saving')
    try {
      await patch('/settings', { retention_days: value })
      setState('saved')
      settings.reload()
      summary.reload()
    } catch (e) {
      setState('error')
      setMsg(errText(e))
      setDays(null)
    }
  }

  async function deleteAll() {
    setDeleting(true)
    setDelError(null)
    try {
      const res = await post<{ deleted: Summary['counts'] }>('/data/delete-all', { confirm: 'DELETE' })
      setDeleted(res.deleted)
      setConfirmText('')
      summary.reload()
    } catch (e) {
      setDelError(errText(e))
    } finally {
      setDeleting(false)
    }
  }

  const s = summary.data
  let oldest = ''
  if (s) {
    if (!s.oldest_record) oldest = 'no records yet'
    else if (meta.data && s.oldest_record.slice(0, 10) === meta.data.today) oldest = `oldest from today ${clock(s.oldest_record)}`
    else oldest = `oldest from ${dayLabel(s.oldest_record)} ${clock(s.oldest_record)}`
  }

  return (
    <section className="panel set-section" id="records" aria-labelledby="h-records">
      <div className="panel-head"><h2 id="h-records">Records</h2></div>
      {settings.loading && !settings.data ? <Loading /> : settings.error && !settings.data ? (
        <Failed message={settings.error} onRetry={settings.reload} />
      ) : (
        <div className="panel-pad set-stack">
          <div className="set-row">
            <div className="field set-inline-field">
              <label htmlFor="retention">Records are kept for</label>
              <select id="retention" className="select" value={current ?? 30} disabled={state === 'saving'}
                onChange={(e) => save(Number(e.target.value))}>
                {RETENTION_CHOICES.map((d) => <option key={d} value={d}>{d} days</option>)}
                {current !== null && !RETENTION_CHOICES.includes(current) && <option value={current}>{current} days</option>}
              </select>
            </div>
            <SaveNote state={state} msg={msg} />
          </div>
          <p className="set-hint">Older records are removed automatically.</p>
          {summary.error && !s ? <Failed message={summary.error} onRetry={summary.reload} /> : !s ? (
            <div className="skeleton" style={{ height: 22 }} />
          ) : (
            <p className="set-summary">
              Stored now: {num(s.counts.queries)} lookups, {num(s.counts.alerts)} {s.counts.alerts === 1 ? 'alert' : 'alerts'},{' '}
              {num(s.counts.approval_requests)} payment {s.counts.approval_requests === 1 ? 'request' : 'requests'}; {oldest}.
            </p>
          )}
        </div>
      )}

      <div className="set-danger">
        <div className="set-danger-head">
          <Trash2 aria-hidden="true" />
          <h3>Delete everything</h3>
        </div>
        <p>This deletes all lookups, alerts, payment requests and pauses. It cannot be undone.</p>
        <p className="set-hint">Stays: parents, children, devices, rules and schedules.</p>
        <div className="set-confirm">
          <div className="field">
            <label htmlFor="delete-confirm">Type DELETE to confirm</label>
            <input id="delete-confirm" className="input mono" autoComplete="off" spellCheck={false} value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)} disabled={deleting} />
          </div>
          <button className="btn btn-danger" disabled={confirmText !== 'DELETE' || deleting} onClick={deleteAll}>
            <Trash2 /> {deleting ? 'Deleting…' : 'Delete everything'}
          </button>
        </div>
        {delError && (
          <div className="callout callout-error" role="alert"><AlertCircle /> <span>{delError}</span></div>
        )}
        {deleted && (
          <div className="callout callout-info" role="status">
            <AlertCircle />
            <span>
              Deleted {num(deleted.queries)} lookups, {num(deleted.alerts)} {deleted.alerts === 1 ? 'alert' : 'alerts'},{' '}
              {num(deleted.approval_requests)} payment {deleted.approval_requests === 1 ? 'request' : 'requests'} and{' '}
              {num(deleted.pauses)} {deleted.pauses === 1 ? 'pause' : 'pauses'}.
            </span>
          </div>
        )}
      </div>
    </section>
  )
}

/* ---- 3. Payment approvals ---- */
function Approvals({ settings }: { settings: SettingsPoll }) {
  const [value, setValue] = useState<number | null>(null)
  const [state, setState] = useState<SaveState>('idle')
  const [msg, setMsg] = useState('')
  const current = value ?? settings.data?.approval_minutes_default ?? null

  async function save(v: number) {
    setValue(v)
    setState('saving')
    try {
      await patch('/settings', { approval_minutes_default: v })
      setState('saved')
      settings.reload()
    } catch (e) {
      setState('error')
      setMsg(errText(e))
      setValue(null)
    }
  }

  return (
    <section className="panel set-section" id="approvals" aria-labelledby="h-approvals">
      <div className="panel-head"><h2 id="h-approvals">Payment approvals</h2></div>
      {settings.loading && !settings.data ? <Loading rows={1} /> : settings.error && !settings.data ? (
        <Failed message={settings.error} onRetry={settings.reload} />
      ) : (
        <div className="panel-pad set-stack">
          <div className="set-row">
            <div className="field set-inline-field">
              <label htmlFor="approval-default">Default approval time</label>
              <select id="approval-default" className="select" value={current ?? 30} disabled={state === 'saving'}
                onChange={(e) => save(Number(e.target.value))}>
                {APPROVAL_CHOICES.map((m) => <option key={m} value={m}>{m} minutes</option>)}
                {current !== null && !APPROVAL_CHOICES.includes(current) && <option value={current}>{current} minutes</option>}
              </select>
            </div>
            <SaveNote state={state} msg={msg} />
          </div>
          <p className="set-hint">
            When you approve a store or payment site, access stays open this long. You can pick another time on each request.
          </p>
        </div>
      )}
    </section>
  )
}

/* ---- 4. Family notice ---- */
function FamilyNotice({ consent }: { consent: ConsentPoll }) {
  const { data, error, loading, reload } = consent
  const [tab, setTab] = useState(0)
  const [copied, setCopied] = useState(false)
  const [copyError, setCopyError] = useState<string | null>(null)
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [wError, setWError] = useState<string | null>(null)

  const notice = data?.notice[tab] ?? data?.notice[0]

  async function copy() {
    if (!notice) return
    try {
      await navigator.clipboard.writeText(notice.text)
      setCopied(true)
      setCopyError(null)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopyError('Copying is blocked in this browser. Select the text and copy it instead.')
    }
  }

  async function withdraw() {
    setBusy(true)
    setWError(null)
    try {
      await post('/consent/withdraw')
      window.location.reload()
    } catch (e) {
      setWError(errText(e))
      setBusy(false)
    }
  }

  let confirmedLine = ''
  if (data?.confirmed && data.confirmed_at) {
    confirmedLine = `Confirmed${data.confirmed_by ? ` by ${data.confirmed_by}` : ''} on ${dayLabel(data.confirmed_at)} at ${clock(data.confirmed_at)}`
  } else if (data && !data.confirmed) confirmedLine = 'Not confirmed yet.'

  return (
    <section className="panel set-section" id="family-notice" aria-labelledby="h-notice">
      <div className="panel-head"><h2 id="h-notice">Family notice</h2></div>
      {loading && !data ? <Loading rows={4} /> : error && !data ? <Failed message={error} onRetry={reload} /> : data && (
        <>
          <div className="panel-pad set-intro">
            <p>The note you can read to your children, print or send. One for each child.</p>
          </div>
          {data.notice.length > 1 && (
            <div className="tabs" role="tablist" aria-label="Notice for">
              {data.notice.map((x, i) => (
                <button key={x.child_id} role="tab" aria-selected={tab === i} className="tab" onClick={() => setTab(i)}>
                  For {x.child_name}
                </button>
              ))}
            </div>
          )}
          <div className="notice-text set-notice-text">
            {notice
              ? notice.text.split('\n').map((line, i) => (line.trim() ? <p key={i}>{line}</p> : null))
              : <p>No children are set up yet, so there is no notice to show.</p>}
          </div>
          <div className="set-actions">
            <button className="btn btn-secondary" onClick={copy} disabled={!notice}>
              <Copy /> {copied ? 'Copied' : 'Copy text'}
            </button>
            <button className="btn btn-secondary" onClick={() => window.print()} disabled={!notice}>
              <Printer /> Print
            </button>
          </div>
          {copyError && (
            <div className="panel-pad set-tight">
              <div className="callout callout-error" role="alert"><AlertCircle /> <span>{copyError}</span></div>
            </div>
          )}

          <div className="set-consent">
            <p className="set-confirmed">{confirmedLine}</p>
            {!asking ? (
              <button className="btn btn-secondary" onClick={() => setAsking(true)} disabled={!data.confirmed}>
                Withdraw confirmation
              </button>
            ) : (
              <div className="set-withdraw" role="group" aria-label="Withdraw confirmation">
                <p>The dashboard will lock until a parent confirms again. Withdraw the confirmation?</p>
                <div className="set-actions-inline">
                  <button className="btn btn-danger" onClick={withdraw} disabled={busy}>
                    {busy ? 'Withdrawing…' : 'Yes, withdraw'}
                  </button>
                  <button className="btn btn-ghost" onClick={() => { setAsking(false); setWError(null) }} disabled={busy}>
                    Keep it
                  </button>
                </div>
              </div>
            )}
            {wError && <div className="callout callout-error" role="alert"><AlertCircle /> <span>{wError}</span></div>}
          </div>
        </>
      )}
    </section>
  )
}

/* ---- 5. Parents ---- */
function ParentsSection() {
  const parents = usePoll<ParentsData>('/auth/parents', 0)
  const [name, setName] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pwTouched, setPwTouched] = useState(false)
  const [added, setAdded] = useState<string | null>(null)

  const { data } = parents
  const full = data ? data.parents.length >= data.max : false
  const pwShort = password.length < 8
  const canSubmit = name.trim() !== '' && username.trim() !== '' && !pwShort && !busy

  async function submit(e: FormEvent) {
    e.preventDefault()
    setPwTouched(true)
    if (!canSubmit) {
      if (!name.trim() || !username.trim()) setError('Enter a display name and a username.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await post('/auth/parents', { username: username.trim(), display_name: name.trim(), password })
      setAdded(name.trim())
      setName('')
      setUsername('')
      setPassword('')
      setShow(false)
      setPwTouched(false)
      parents.reload()
    } catch (err) {
      setError(errText(err))
      if (err instanceof ApiError && err.status === 409) parents.reload()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel set-section" id="parents" aria-labelledby="h-parents">
      <div className="panel-head"><h2 id="h-parents">Parents</h2></div>
      {parents.loading && !data ? <Loading /> : parents.error && !data ? (
        <Failed message={parents.error} onRetry={parents.reload} />
      ) : data && (
        <>
          <ul className="set-parents">
            {data.parents.map((p) => (
              <li key={p.id}>
                <span className="set-parent-name">{p.display_name}</span>
                <span className="mono set-parent-user">{p.username}</span>
              </li>
            ))}
          </ul>
          {added && <p className="set-note set-pad-x" role="status">Added {added}.</p>}
          {full ? (
            <div className="panel-pad">
              <p className="set-hint">This home has the maximum of {data.max} parent accounts.</p>
            </div>
          ) : (
            <form className="panel-pad set-form" onSubmit={submit} noValidate>
              <h3>Add a parent</h3>
              <div className="set-form-grid">
                <div className="field">
                  <label htmlFor="p-name">Display name</label>
                  <input id="p-name" className="input" value={name} onChange={(e) => setName(e.target.value)}
                    autoComplete="off" disabled={busy} />
                </div>
                <div className="field">
                  <label htmlFor="p-user">Username</label>
                  <input id="p-user" className="input mono" value={username} onChange={(e) => setUsername(e.target.value)}
                    autoComplete="off" autoCapitalize="none" spellCheck={false} disabled={busy} />
                </div>
                <div className="field">
                  <label htmlFor="p-pass">Password</label>
                  <div className="set-pass">
                    <input id="p-pass" className="input" type={show ? 'text' : 'password'} value={password}
                      onChange={(e) => setPassword(e.target.value)} onBlur={() => setPwTouched(true)}
                      autoComplete="new-password" aria-invalid={pwTouched && pwShort} aria-describedby="p-pass-hint"
                      disabled={busy} />
                    <button type="button" className="btn btn-ghost btn-icon" onClick={() => setShow((v) => !v)}
                      aria-label={show ? 'Hide password' : 'Show password'} aria-pressed={show}>
                      {show ? <EyeOff /> : <Eye />}
                    </button>
                  </div>
                  <span id="p-pass-hint" className="set-hint" data-kind={pwTouched && pwShort ? 'error' : undefined}>
                    At least 8 characters.
                  </span>
                </div>
              </div>
              {error && <div className="callout callout-error" role="alert"><AlertCircle /> <span>{error}</span></div>}
              <div>
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  <UserPlus /> {busy ? 'Adding…' : 'Add parent'}
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </section>
  )
}

export default function Settings() {
  const { title, what } = SCREEN_INFO.settings
  const settings = usePoll<SettingsData>('/settings', 0)
  const consent = usePoll<ConsentData>('/consent', 0)
  const [active, setActive] = useState(SECTIONS[0].id)

  useEffect(() => {
    if (!('IntersectionObserver' in window)) return
    const els = SECTIONS.map((s) => document.getElementById(s.id)).filter((x): x is HTMLElement => !!x)
    const io = new IntersectionObserver(
      (entries) => {
        const hit = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (hit) setActive(hit.target.id)
      },
      { rootMargin: '-80px 0px -60% 0px' },
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>{what}</p>
        </div>
      </div>
      <div className="set-layout">
        <nav className="set-nav" aria-label="Settings sections">
          {SECTIONS.map((s) => (
            <a key={s.id} href={`#${s.id}`} aria-current={active === s.id ? 'true' : undefined}
              onClick={(e) => {
                e.preventDefault()
                setActive(s.id)
                document.getElementById(s.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }}>
              {s.label}
            </a>
          ))}
        </nav>
        <div className="set-content">
          <DoesNotSee consent={consent} />
          <Records settings={settings} />
          <Approvals settings={settings} />
          <FamilyNotice consent={consent} />
          <ParentsSection />
        </div>
      </div>
    </div>
  )
}
