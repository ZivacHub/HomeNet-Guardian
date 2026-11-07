import { AlertTriangle, Gamepad2, HelpCircle, Laptop, Smartphone, Tablet, Tv, type LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { post } from '../lib/api'
import { ago, categoryLabel, clock, minutes } from '../lib/format'
import { href } from '../lib/routes'
import { usePoll } from '../lib/usePoll'
import { SCREEN_INFO } from './screenInfo'
import '../styles/pages/overview.css'

type OnlineDevice = { id: number; display_name: string; kind: string; child_id: number | null; child_name: string | null; last_seen: string }
type ChildToday = {
  id: number
  name: string
  lookups: number
  blocked: number
  estimated_minutes: number
  top_categories: { category: string; minutes: number }[]
}
type Alert = { id: number; ts: string; kind: string; severity: string; device_id: number | null; message: string; acknowledged: boolean }
type OverviewData = {
  now: string
  online_devices: OnlineDevice[]
  children: ChildToday[]
  unacknowledged_alerts: number
  newest_alerts: Alert[]
  pending_approvals: number
  estimate_note: string
}
type Device = {
  id: number
  display_name: string
  kind: string
  owner: string
  child_id: number | null
  child_name: string | null
  known: boolean
  last_seen: string
}
type Children = { items: { id: number; name: string; age: number }[] }

const KIND_ICON: Record<string, LucideIcon> = {
  phone: Smartphone, tablet: Tablet, laptop: Laptop, tv: Tv, console: Gamepad2, unknown: HelpCircle,
}
const SEVERITY: Record<string, { cls: string; label: string }> = {
  critical: { cls: 'badge-block', label: 'Important' },
  warning: { cls: 'badge-warn', label: 'Check' },
  info: { cls: 'badge-info', label: 'Info' },
}
const ALERT_LINK: Record<string, { to: 'payments' | 'devices' | 'activity'; label: string }> = {
  approval_waiting: { to: 'payments', label: 'Review request' },
  new_device: { to: 'devices', label: 'Assign device' },
  dns_bypass: { to: 'activity', label: 'See activity' },
  night_use: { to: 'activity', label: 'See activity' },
  explicit_blocked: { to: 'activity', label: 'See activity' },
}
const PEOPLE = ['Mom', 'Dad', 'Ana', 'Luka']
const ONLINE_WINDOW_MIN = 10

const isOnline = (lastSeen: string, now: string) => (Date.parse(now) - Date.parse(lastSeen)) / 60000 <= ONLINE_WINDOW_MIN

function dayAndTime(now: string) {
  const d = new Date(now)
  const day = d.toLocaleDateString('en-GB', { weekday: 'long' })
  return `${day} ${clock(now)}`
}

function DeviceChip({ d, now }: { d: Device; now: string }) {
  const Icon = KIND_ICON[d.kind] ?? HelpCircle
  const online = isOnline(d.last_seen, now)
  return (
    <li className={`ov-chip${online ? ' is-on' : ''}`}>
      <span className="ov-led" role="img" aria-label={online ? 'Online' : 'Offline'} />
      <Icon aria-hidden="true" />
      <span className="ov-chip-name">{d.display_name}</span>
      {!online && <span className="ov-chip-seen">last seen {clock(d.last_seen)}</span>}
      {!d.known && (
        <a className="badge badge-warn ov-new" href={href('devices')}>
          New
        </a>
      )}
    </li>
  )
}

function HomeNow({ devices, ages, now }: { devices: Device[]; ages: Record<string, number>; now: string }) {
  const groups = new Map<string, Device[]>()
  for (const d of devices) {
    const who = d.child_name || d.owner || 'Not assigned'
    groups.set(who, [...(groups.get(who) ?? []), d])
  }
  const order = [...PEOPLE, ...[...groups.keys()].filter((k) => !PEOPLE.includes(k) && k !== 'Not assigned'), 'Not assigned']
  const rows = order.filter((k) => groups.has(k) || PEOPLE.includes(k) || k === 'Not assigned')
  const online = devices.filter((d) => isOnline(d.last_seen, now)).length
  return (
    <section className="panel ov-home" aria-labelledby="ov-home-h">
      <div className="panel-head">
        <h2 id="ov-home-h">At home right now</h2>
        <span className="ov-sub num">
          {online} of {devices.length} devices online
        </span>
      </div>
      <ul className="ov-rows">
        {rows.map((who) => {
          const list = groups.get(who) ?? []
          return (
            <li key={who} className="ov-row">
              <div className="ov-who">
                <span className="ov-name">{who}</span>
                {ages[who] != null && <span className="ov-age num">{ages[who]}</span>}
              </div>
              {list.length ? (
                <ul className="ov-chips">
                  {list.map((d) => (
                    <DeviceChip key={d.id} d={d} now={now} />
                  ))}
                </ul>
              ) : (
                <span className="ov-none">No devices</span>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

function TodayPanel({ c, note }: { c: ChildToday; note: string }) {
  const max = Math.max(1, ...c.top_categories.slice(0, 3).map((t) => t.minutes))
  return (
    <section className="panel ov-today" aria-labelledby={`ov-t-${c.id}`}>
      <div className="panel-head">
        <h2 id={`ov-t-${c.id}`}>{c.name} today</h2>
        {c.blocked > 0 ? (
          <span className="badge badge-block num">{c.blocked} blocked</span>
        ) : (
          <span className="badge badge-plain num">0 blocked</span>
        )}
      </div>
      <div className="panel-pad">
        <p className="ov-time">
          About <strong className="num">{minutes(c.estimated_minutes)}</strong> online <span className="ov-est">(estimate)</span>
        </p>
        <p className="ov-lookups num">{c.lookups} site lookups</p>
        <ul className="ov-bars" aria-label={`Top categories for ${c.name}`}>
          {c.top_categories.slice(0, 3).map((t) => (
            <li key={t.category} className="ov-bar">
              <span className="ov-bar-label">{categoryLabel(t.category)}</span>
              <span className="ov-bar-track" aria-hidden="true">
                <span className="ov-bar-fill" style={{ transform: `scaleX(${Math.max(0.03, t.minutes / max)})` }} />
              </span>
              <span className="ov-bar-min num">{minutes(t.minutes)}</span>
            </li>
          ))}
        </ul>
        <p className="ov-note">{note}</p>
        <a className="btn btn-secondary ov-link" href={href('time')}>
          See where time goes
        </a>
      </div>
    </section>
  )
}

function Attention({ data, onChanged }: { data: OverviewData; onChanged: () => void }) {
  const [busy, setBusy] = useState<number | null>(null)
  const [err, setErr] = useState<string | null>(null)
  async function ack(id: number) {
    setBusy(id)
    setErr(null)
    try {
      await post(`/alerts/${id}/ack`)
      onChanged()
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not mark this as seen.')
    } finally {
      setBusy(null)
    }
  }
  const alerts = data.newest_alerts.filter((a) => !a.acknowledged)
  const waiting = data.pending_approvals
  return (
    <section className="panel ov-attn" aria-labelledby="ov-attn-h">
      <div className="panel-head">
        <h2 id="ov-attn-h">Needs your attention</h2>
        {data.unacknowledged_alerts > alerts.length && (
          <span className="ov-sub num">Showing {alerts.length} of {data.unacknowledged_alerts}</span>
        )}
      </div>
      <div className="ov-attn-body">
        {waiting > 0 && (
          <div className="callout callout-warn">
            <AlertTriangle aria-hidden="true" />
            <span className="ov-callout-text">
              {waiting === 1 ? '1 store or payment request is waiting for your OK.' : `${waiting} store or payment requests are waiting for your OK.`}
            </span>
            <a className="btn btn-primary ov-callout-btn" href={href('payments')}>
              Review requests
            </a>
          </div>
        )}
        {err && <div className="callout callout-error" role="alert">{err}</div>}
        {alerts.length === 0 ? (
          <div className="empty ov-empty">
            <h3>Nothing needs you right now.</h3>
            <p>New devices, store requests, late-night use and attempts to dodge the filter will show up here.</p>
          </div>
        ) : (
          <ul className="ov-alerts">
            {alerts.map((a) => {
              const sev = SEVERITY[a.severity] ?? SEVERITY.info
              const link = ALERT_LINK[a.kind]
              return (
                <li key={a.id} className="ov-alert">
                  <div className="ov-alert-meta">
                    <span className="ov-alert-time num">{clock(a.ts)}</span>
                    <span className={`badge ${sev.cls}`}>{sev.label}</span>
                    {!ago(a.ts, data.now).startsWith('at ') && (
                      <span className="ov-alert-ago">{ago(a.ts, data.now)}</span>
                    )}
                  </div>
                  <p className="ov-alert-msg">{a.message}</p>
                  <div className="ov-alert-actions">
                    {link && (
                      <a className="btn btn-secondary" href={href(link.to)}>
                        {link.label}
                      </a>
                    )}
                    <button className="btn btn-ghost" disabled={busy === a.id} onClick={() => ack(a.id)}>
                      {busy === a.id ? 'Saving…' : 'Mark as seen'}
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </section>
  )
}

function Loading() {
  return (
    <div className="ov-grid" aria-busy="true" aria-label="Loading overview">
      <div className="panel ov-home panel-pad">
        <div className="skeleton ov-sk" style={{ height: 22, width: 180 }} />
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="skeleton ov-sk" style={{ height: 36 }} />
        ))}
      </div>
      {[0, 1].map((i) => (
        <div key={i} className="panel panel-pad">
          <div className="skeleton ov-sk" style={{ height: 22, width: 140 }} />
          <div className="skeleton ov-sk" style={{ height: 18, width: '70%' }} />
          <div className="skeleton ov-sk" style={{ height: 60 }} />
        </div>
      ))}
      <div className="panel ov-attn panel-pad">
        <div className="skeleton ov-sk" style={{ height: 22, width: 200 }} />
        <div className="skeleton ov-sk" style={{ height: 56 }} />
      </div>
    </div>
  )
}

export default function Overview() {
  const info = SCREEN_INFO.overview
  const ov = usePoll<OverviewData>('/overview')
  const dev = usePoll<{ items: Device[] }>('/devices')
  const kids = usePoll<Children>('/children', 0)

  const error = ov.error || dev.error
  const ready = ov.data && dev.data
  const ages: Record<string, number> = {}
  kids.data?.items.forEach((c) => { ages[c.name] = c.age })

  const reloadAll = () => { ov.reload(); dev.reload() }

  return (
    <div className="page ov">
      <header className="page-head">
        <div>
          <h1>{info.title}</h1>
          <p>{info.what}</p>
        </div>
        {ov.data && <span className="ov-clock num">{dayAndTime(ov.data.now)}</span>}
      </header>

      {error && !ready ? (
        <div className="callout callout-error" role="alert">
          <AlertTriangle aria-hidden="true" />
          <span className="ov-callout-text">{error}</span>
          <button className="btn btn-secondary" onClick={reloadAll}>Try again</button>
        </div>
      ) : !ready ? (
        <Loading />
      ) : (
        <div className="ov-grid">
          <HomeNow devices={dev.data!.items} ages={ages} now={ov.data!.now} />
          {ov.data!.children.map((c) => (
            <TodayPanel key={c.id} c={c} note={ov.data!.estimate_note} />
          ))}
          <Attention data={ov.data!} onChanged={reloadAll} />
        </div>
      )}
    </div>
  )
}
