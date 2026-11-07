import { useEffect, useMemo, useRef, useState } from 'react'
import type { ComponentType } from 'react'
import { AlertTriangle, Check, Gamepad2, HelpCircle, Laptop, Pencil, Smartphone, Tablet, Tv, X } from 'lucide-react'
import { ApiError, patch } from '../lib/api'
import { clock } from '../lib/format'
import { usePoll } from '../lib/usePoll'
import { SCREEN_INFO } from './screenInfo'
import '../styles/pages/devices.css'

type Device = {
  id: number; mac: string; hostname: string; display_name: string; kind: string; owner: string
  child_id: number | null; known: boolean; last_seen: string; child_name: string | null
  lookups_today: number; online: boolean
}
type Child = { id: number; name: string; age: number; age_profile: number; profile_label: string }
type Meta = { age_profiles: { age_profile: number; label: string }[] }

const KIND_ICON: Record<string, ComponentType<{ 'aria-hidden'?: boolean }>> = {
  phone: Smartphone, tablet: Tablet, laptop: Laptop, tv: Tv, console: Gamepad2, unknown: HelpCircle,
}

type Note = { kind: 'saved' | 'error'; text: string }
const errText = (e: unknown) => (e instanceof ApiError ? e.message : 'The change could not be saved.')
const without = <T,>(o: Record<string, T>, key: string) => {
  const rest = { ...o }
  delete rest[key]
  return rest
}

export default function Devices() {
  const { title, what } = SCREEN_INFO.devices
  const devs = usePoll<{ items: Device[] }>('/devices')
  const kids = usePoll<{ items: Child[] }>('/children', 0)
  const meta = usePoll<Meta>('/meta', 0)

  const [busy, setBusy] = useState<Set<string>>(new Set())
  const [notes, setNotes] = useState<Record<string, Note>>({})
  const [pending, setPending] = useState<Record<string, string>>({})
  const [renaming, setRenaming] = useState<number | null>(null)
  const [draft, setDraft] = useState('')
  const timers = useRef<number[]>([])
  useEffect(() => () => timers.current.forEach(window.clearTimeout), [])

  const setBusyKey = (key: string, on: boolean) =>
    setBusy((s) => {
      const n = new Set(s)
      if (on) n.add(key)
      else n.delete(key)
      return n
    })

  async function save(key: string, path: string, body: unknown, after?: () => void) {
    setBusyKey(key, true)
    setNotes((n) => without(n, key))
    try {
      await patch(path, body)
      await Promise.all([devs.reload(), kids.reload()])
      setNotes((n) => ({ ...n, [key]: { kind: 'saved', text: 'Saved' } }))
      timers.current.push(
        window.setTimeout(() => setNotes((n) => (n[key]?.kind === 'saved' ? without(n, key) : n)), 2500),
      )
      after?.()
    } catch (e) {
      setNotes((n) => ({ ...n, [key]: { kind: 'error', text: errText(e) } }))
    } finally {
      setPending((p) => without(p, key))
      setBusyKey(key, false)
    }
  }

  const rows = useMemo(() => {
    const list = [...(devs.data?.items ?? [])]
    return list.sort(
      (a, b) =>
        Number(a.known) - Number(b.known) ||
        Number(b.online) - Number(a.online) ||
        a.display_name.localeCompare(b.display_name),
    )
  }, [devs.data])

  const total = rows.length
  const fresh = rows.filter((d) => !d.known).length
  const children = kids.data?.items ?? []
  const profiles = meta.data?.age_profiles ?? []

  function startRename(d: Device) {
    setRenaming(d.id)
    setDraft(d.display_name)
  }
  const cancelRename = () => setRenaming(null)
  function commitRename(d: Device) {
    const name = draft.trim()
    if (name.length < 1 || name.length > 60) return
    if (name === d.display_name) return cancelRename()
    save(`n${d.id}`, `/devices/${d.id}`, { display_name: name }, cancelRename)
  }

  const showError = devs.error && !devs.data

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>{what}</p>
        </div>
        {devs.data && (
          <div className="dev-count num" aria-live="polite">
            <strong>{total - fresh}</strong> known
            {fresh > 0 && (
              <>
                {' · '}
                <strong>{fresh}</strong> new
              </>
            )}
          </div>
        )}
      </div>

      {showError && (
        <div className="callout callout-error" role="alert">
          <AlertTriangle aria-hidden />
          <div>
            {devs.error}{' '}
            <button type="button" className="btn btn-secondary" onClick={() => devs.reload()}>
              Try again
            </button>
          </div>
        </div>
      )}

      {fresh > 0 && (
        <div className="callout callout-warn dev-warn" role="status">
          <AlertTriangle aria-hidden />
          <div>A device you have not seen before joined the Wi-Fi. Assign it to someone, or mark it as known.</div>
        </div>
      )}

      {!showError && (
        <div className="dev-stack">
          <section className="panel" aria-label="Devices">
            {devs.loading && !devs.data ? (
              <div aria-busy="true" aria-label="Loading devices">
                {[0, 1, 2, 3, 4].map((i) => (
                  <div className="dev-skel-row" key={i}>
                    <div className="skeleton" style={{ width: 32, height: 32 }} />
                    <div className="skeleton" style={{ width: '30%', height: 14 }} />
                    <div className="skeleton" style={{ width: '20%', height: 14 }} />
                    <div className="skeleton" style={{ width: '12%', height: 14 }} />
                  </div>
                ))}
              </div>
            ) : rows.length === 0 ? (
              <div className="empty">
                <h2>No devices yet</h2>
                <p>Devices appear here as soon as they join the Wi-Fi.</p>
              </div>
            ) : (
              <>
                <div className="table-wrap">
                  <table className="table dev-table">
                    <thead>
                      <tr>
                        <th>Device</th>
                        <th>Status</th>
                        <th>Belongs to</th>
                        <th className="num">Lookups today</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((d) => {
                        const Icon = KIND_ICON[d.kind] ?? HelpCircle
                        const ownKey = `c${d.id}`
                        const nameKey = `n${d.id}`
                        const knownKey = `k${d.id}`
                        const ownNote = notes[ownKey]
                        const nameNote = notes[nameKey]
                        const knownNote = notes[knownKey]
                        const actionNote = knownNote ?? nameNote
                        const selectVal = pending[ownKey] ?? (d.child_id == null ? '' : String(d.child_id))
                        return (
                          <tr key={d.id}>
                            <td>
                              <div className="dev-device">
                                <span className="dev-icon">
                                  <Icon aria-hidden />
                                </span>
                                <div>
                                  <div className="dev-name">{d.display_name}</div>
                                  <span className="dev-meta">
                                    <span className="mono">{d.hostname}</span>
                                    <span className="mono">{d.mac}</span>
                                  </span>
                                </div>
                              </div>
                            </td>
                            <td>
                              <div className="dev-status">
                                {d.online ? (
                                  <span className="badge badge-ok">Online</span>
                                ) : (
                                  <span className="badge badge-plain">Offline · last seen {clock(d.last_seen)}</span>
                                )}
                                {!d.known && <span className="badge badge-warn">New</span>}
                              </div>
                            </td>
                            <td>
                              <div className="dev-owner">
                                <select
                                  className="select"
                                  aria-label={`Who ${d.display_name} belongs to`}
                                  value={selectVal}
                                  disabled={busy.has(ownKey)}
                                  onChange={(e) => {
                                    const v = e.target.value
                                    setPending((p) => ({ ...p, [ownKey]: v }))
                                    save(ownKey, `/devices/${d.id}`, { child_id: v === '' ? null : Number(v) })
                                  }}
                                >
                                  <option value="">{d.owner || 'Not assigned'}</option>
                                  {children.map((c) => (
                                    <option key={c.id} value={c.id}>
                                      {c.name} ({c.age})
                                    </option>
                                  ))}
                                </select>
                                {ownNote && (
                                  <span
                                    className="dev-note"
                                    data-kind={ownNote.kind}
                                    role={ownNote.kind === 'error' ? 'alert' : 'status'}
                                  >
                                    {ownNote.text}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="num">{d.lookups_today}</td>
                            <td>
                              {renaming === d.id ? (
                                <div className="dev-rename">
                                  <div className="dev-rename-row">
                                    <input
                                      className="input"
                                      aria-label={`New name for ${d.display_name}`}
                                      value={draft}
                                      maxLength={60}
                                      autoFocus
                                      disabled={busy.has(nameKey)}
                                      aria-invalid={draft.trim().length < 1}
                                      onChange={(e) => setDraft(e.target.value)}
                                      onKeyDown={(e) => {
                                        if (e.key === 'Enter') commitRename(d)
                                        if (e.key === 'Escape') cancelRename()
                                      }}
                                    />
                                    <button
                                      type="button"
                                      className="btn btn-primary"
                                      disabled={busy.has(nameKey) || draft.trim().length < 1}
                                      onClick={() => commitRename(d)}
                                    >
                                      <Check aria-hidden /> Save
                                    </button>
                                    <button
                                      type="button"
                                      className="btn btn-ghost"
                                      disabled={busy.has(nameKey)}
                                      onClick={cancelRename}
                                    >
                                      <X aria-hidden /> Cancel
                                    </button>
                                  </div>
                                  {nameNote?.kind === 'error' && (
                                    <span className="dev-note" data-kind="error" role="alert">
                                      {nameNote.text}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <div className="dev-actions">
                                  <button type="button" className="btn btn-secondary" onClick={() => startRename(d)}>
                                    <Pencil aria-hidden /> Rename
                                  </button>
                                  {!d.known && (
                                    <button
                                      type="button"
                                      className="btn btn-primary"
                                      disabled={busy.has(knownKey)}
                                      onClick={() => save(knownKey, `/devices/${d.id}`, { known: true })}
                                    >
                                      <Check aria-hidden /> Mark as known
                                    </button>
                                  )}
                                  {actionNote && (
                                    <span
                                      className="dev-note"
                                      data-kind={actionNote.kind}
                                      role={actionNote.kind === 'error' ? 'alert' : 'status'}
                                    >
                                      {actionNote.text}
                                    </span>
                                  )}
                                </div>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                <p className="dev-foot">
                  Devices assigned to a child follow that child&rsquo;s rules (age profile, bedtime, blocked
                  categories).
                </p>
              </>
            )}
          </section>

          <section className="panel" aria-label="Children and age profiles">
            <div className="panel-head">
              <h2>Children and age profiles</h2>
            </div>
            {!kids.data && kids.error ? (
              <div className="panel-pad">
                <div className="callout callout-error" role="alert">
                  <AlertTriangle aria-hidden />
                  <div>
                    {kids.error}{' '}
                    <button type="button" className="btn btn-secondary" onClick={() => kids.reload()}>
                      Try again
                    </button>
                  </div>
                </div>
              </div>
            ) : !kids.data ? (
              <div aria-busy="true" aria-label="Loading children">
                {[0, 1].map((i) => (
                  <div className="dev-skel-row" key={i}>
                    <div className="skeleton" style={{ width: '40%', height: 16 }} />
                  </div>
                ))}
              </div>
            ) : (
              <>
                <ul className="dev-kids">
                  {children.map((c) => {
                    const key = `p${c.id}`
                    const note = notes[key]
                    const options = profiles.length
                      ? profiles
                      : [{ age_profile: c.age_profile, label: c.profile_label }]
                    return (
                      <li className="dev-kid" key={c.id}>
                        <div>
                          <span className="dev-kid-name">{c.name}</span>
                          <span className="dev-kid-age num">{c.age} years old</span>
                        </div>
                        <div className="dev-kid-ctl">
                          <select
                            className="select"
                            aria-label={`Age profile for ${c.name}`}
                            value={pending[key] ?? String(c.age_profile)}
                            disabled={busy.has(key)}
                            onChange={(e) => {
                              const v = e.target.value
                              setPending((p) => ({ ...p, [key]: v }))
                              save(key, `/children/${c.id}`, { age_profile: Number(v) })
                            }}
                          >
                            {options.map((p) => (
                              <option key={p.age_profile} value={p.age_profile}>
                                {p.label}
                              </option>
                            ))}
                          </select>
                          {note && (
                            <span
                              className="dev-note"
                              data-kind={note.kind}
                              role={note.kind === 'error' ? 'alert' : 'status'}
                            >
                              {note.text}
                            </span>
                          )}
                        </div>
                      </li>
                    )
                  })}
                </ul>
                <p className="dev-foot">
                  The age profile sets the starting rules, like bedtime and blocked categories. You can change each
                  rule on the Rules page. Changing the profile here updates the profile only; existing rules stay as
                  they are, so adjust them on Rules.
                </p>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
