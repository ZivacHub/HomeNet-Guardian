import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, Info, ShieldAlert, X } from 'lucide-react'
import { ApiError, post } from '../lib/api'
import { clock } from '../lib/format'
import { usePoll } from '../lib/usePoll'
import { Domain } from '../components/Domain'
import { SCREEN_INFO } from './screenInfo'
import '../styles/pages/payments.css'

type Approval = {
  id: number; ts: string; device_id: number; domain: string
  status: 'pending' | 'approved' | 'denied' | 'expired'
  decided_by: number | null; decided_at: string | null; approved_until: string | null
  device_name: string; child_name: string | null
}
type Parent = { id: number; display_name: string }
type Outcome = { kind: 'approved' | 'denied' | 'taken' | 'error'; text: string }

const CHOICES = [15, 30, 60, 120]
const choiceLabel = (m: number) => (m >= 60 ? `${m / 60} h` : `${m} min`)

function waiting(ts: string, now: string): string {
  const m = Math.max(0, Math.floor((Date.parse(now) - Date.parse(ts)) / 60000))
  if (m < 1) return 'waiting less than a minute'
  if (m < 60) return `waiting ${m} min`
  return `waiting ${Math.floor(m / 60)} h ${m % 60} min`
}

const FALLBACK_NOTE =
  "Store and payment blocking works on site names only. Real purchase control lives in the phone's family settings (Apple Ask to Buy, Google Family Link)."

export default function Payments() {
  const { title, what } = SCREEN_INFO.payments
  const list = usePoll<{ items: Approval[]; note: string }>('/approvals')
  const overview = usePoll<{ now: string }>('/overview')
  const parents = usePoll<{ parents: Parent[] }>('/auth/parents', 0)

  const [mins, setMins] = useState<Record<number, number>>({})
  const [busy, setBusy] = useState<Set<number>>(new Set())
  const [outcome, setOutcome] = useState<Record<number, Outcome>>({})
  const timers = useRef<number[]>([])
  useEffect(() => () => timers.current.forEach(window.clearTimeout), [])

  const items = list.data?.items ?? []
  const now = overview.data?.now
  const open = items.filter((a) => a.status === 'pending' || outcome[a.id])
  const waitingCount = items.filter((a) => a.status === 'pending' && !outcome[a.id]).length
  const log = items.filter((a) => a.status !== 'pending' && !outcome[a.id])
  const parentName = useMemo(() => {
    const m = new Map<number, string>()
    parents.data?.parents.forEach((p) => m.set(p.id, p.display_name))
    return m
  }, [parents.data])

  function setOutcomeFor(id: number, o: Outcome | null) {
    setOutcome((prev) => {
      const next = { ...prev }
      if (o) next[id] = o
      else delete next[id]
      return next
    })
  }

  async function decide(a: Approval, approve: boolean) {
    setBusy((s) => new Set(s).add(a.id))
    let result: Outcome
    try {
      if (approve) {
        const r = await post<Approval>(`/approvals/${a.id}/approve`, { minutes: mins[a.id] ?? 30 })
        result = { kind: 'approved', text: `Approved until ${clock(r.approved_until)}` }
      } else {
        await post(`/approvals/${a.id}/deny`)
        result = { kind: 'denied', text: 'Denied' }
      }
    } catch (e) {
      result =
        e instanceof ApiError && e.status === 409
          ? { kind: 'taken', text: 'Someone already answered this request.' }
          : { kind: 'error', text: e instanceof ApiError ? e.message : 'The answer could not be sent. Try again.' }
    }
    setBusy((s) => {
      const n = new Set(s)
      n.delete(a.id)
      return n
    })
    setOutcomeFor(a.id, result)
    if (result.kind === 'error') return
    await list.reload()
    timers.current.push(window.setTimeout(() => setOutcomeFor(a.id, null), 2600))
  }

  const showError = list.error && !list.data
  const first = list.loading && !list.data

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>{what}</p>
        </div>
      </div>

      <div className="callout callout-info pay-note" role="note">
        <Info aria-hidden="true" />
        <span>{list.data?.note ?? FALLBACK_NOTE}</span>
      </div>

      {showError ? (
        <div className="callout callout-error" role="alert">
          <ShieldAlert aria-hidden="true" />
          <span>{list.error}</span>
          <button className="btn btn-secondary pay-retry" onClick={list.reload}>
            Try again
          </button>
        </div>
      ) : (
        <>
          <section className="panel pay-section" aria-labelledby="pay-wait">
            <div className="panel-head">
              <h2 id="pay-wait">Waiting for you</h2>
              {!first && (
                <span className={`badge ${waitingCount ? 'badge-warn' : 'badge-plain'}`}>
                  <span className="num">{waitingCount}</span>&nbsp;waiting
                </span>
              )}
            </div>
            {first ? (
              <div className="pay-skel">
                <div className="skeleton pay-skel-row" />
              </div>
            ) : open.length === 0 ? (
              <div className="empty">
                <h2>No requests are waiting</h2>
                <p>When a child tries a store or payment site, it appears here.</p>
              </div>
            ) : (
              <ul className="pay-list">
                {open.map((a) => {
                  const o = outcome[a.id]
                  const isBusy = busy.has(a.id)
                  const finished = o && (o.kind === 'approved' || o.kind === 'denied')
                  const locked = isBusy || o?.kind === 'taken'
                  return (
                    <li key={a.id} className={`pay-row${finished ? ' pay-row-done' : ''}`}>
                      <div className="pay-what">
                        <p className="pay-device">
                          {a.device_name}
                          {a.child_name && <span className="pay-child"> · {a.child_name}</span>}
                        </p>
                        <p className="pay-site">
                          wants to open <Domain domain={a.domain} category="payments" />
                        </p>
                        <p className="pay-when">
                          Asked at <span className="num">{clock(a.ts)}</span>
                          {now && <> · <span className="num">{waiting(a.ts, now)}</span></>}
                        </p>
                      </div>
                      {finished ? (
                        <p className={`pay-result pay-result-${o.kind}`} role="status">
                          {o.kind === 'approved' ? <Check aria-hidden="true" /> : <X aria-hidden="true" />}
                          {o.text}
                        </p>
                      ) : (
                        <div className="pay-actions">
                          <div className="pay-buttons">
                            <button className="btn btn-primary" disabled={locked} onClick={() => decide(a, true)}>
                              Approve for {choiceLabel(mins[a.id] ?? 30)}
                            </button>
                            <select
                              className="select pay-select"
                              aria-label={`How long to allow for ${a.device_name}`}
                              value={mins[a.id] ?? 30}
                              disabled={locked}
                              onChange={(e) => setMins((m) => ({ ...m, [a.id]: Number(e.target.value) }))}
                            >
                              {CHOICES.map((c) => (
                                <option key={c} value={c}>{choiceLabel(c)}</option>
                              ))}
                            </select>
                            <button className="btn btn-secondary" disabled={locked} onClick={() => decide(a, false)}>
                              Deny
                            </button>
                          </div>
                          {o && (o.kind === 'taken' || o.kind === 'error') && (
                            <p className="pay-msg" role="alert">{o.text}</p>
                          )}
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>
            )}
          </section>

          <section className="panel pay-section" aria-labelledby="pay-log">
            <div className="panel-head">
              <h2 id="pay-log">Decision log</h2>
            </div>
            {first ? (
              <div className="pay-skel">
                <div className="skeleton pay-skel-table" />
              </div>
            ) : log.length === 0 ? (
              <div className="empty">
                <p>No decisions yet. Answered requests are listed here, newest first.</p>
              </div>
            ) : (
              <div className="table-wrap">
                <table className="table pay-log-table">
                  <thead>
                    <tr>
                      <th>Asked</th><th>Device</th><th>Site</th><th>Result</th><th>Decided by</th><th>Allowed until</th>
                    </tr>
                  </thead>
                  <tbody>
                    {log.map((a) => (
                      <tr key={a.id}>
                        <td className="num mono">{clock(a.ts)}</td>
                        <td>{a.device_name}{a.child_name && <span className="pay-child"> · {a.child_name}</span>}</td>
                        <td><Domain domain={a.domain} category="payments" /></td>
                        <td>
                          {a.status === 'approved' && <span className="badge badge-ok">Approved</span>}
                          {a.status === 'denied' && <span className="badge badge-block">Denied</span>}
                          {a.status === 'expired' && <span className="badge badge-plain">Expired</span>}
                        </td>
                        <td>
                          {a.decided_by != null
                            ? parentName.get(a.decided_by) ?? 'A parent'
                            : a.status === 'expired' ? 'Time ran out' : '–'}
                        </td>
                        <td className="num mono">{clock(a.approved_until)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="pay-how" aria-labelledby="pay-how">
            <h2 id="pay-how">How this works</h2>
            <ul>
              <li>A child's device tries a store or payment site. It is blocked and you get a request here.</li>
              <li>You approve for a set time, or deny.</li>
              <li>When the time is over, the site is blocked again and the next try asks you again.</li>
            </ul>
          </section>
        </>
      )}
    </main>
  )
}
