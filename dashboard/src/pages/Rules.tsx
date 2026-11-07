import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { AlertTriangle, Info, Lock, Pause, Pencil, Play, Plus, Trash2, X } from 'lucide-react'
import { ApiError, del, patch, post, put } from '../lib/api'
import { categoryLabel, clock } from '../lib/format'
import { usePoll } from '../lib/usePoll'
import { SCREEN_INFO } from './screenInfo'
import '../styles/pages/rules.css'

type Child = { id: number; name: string; age: number; age_profile: number; profile_label: string }
type RuleRow = { child_id: number | null; category: string; action: 'block' | 'allow' }
type RulesData = { categories: { name: string; fixed: boolean }[]; rules: RuleRow[] }
type Schedule = { id: number; child_id: number; name: string; days: string; start: string; end: string; enabled: boolean }
type PauseRow = { id: number; child_id: number | null; started_at: string; until_ts: string; child_name: string | null }

const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const
const DAY_SHORT: Record<string, string> = { mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu', fri: 'Fri', sat: 'Sat', sun: 'Sun' }
const HIDDEN_CATEGORIES = new Set(['system'])

const errText = (e: unknown, fallback = 'The change could not be saved.') => (e instanceof ApiError ? e.message : fallback)
const targetKey = (id: number | null) => (id === null ? 'home' : String(id))

/** Minutes from the simulated now until the next 07:00 (never more than 1440). */
function minutesToSeven(nowIso: string): { minutes: number; tomorrow: boolean } {
  const now = new Date(nowIso)
  const next = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 7, 0, 0)
  let tomorrow = false
  if (next.getTime() <= now.getTime()) {
    next.setDate(next.getDate() + 1)
    tomorrow = true
  }
  const minutes = Math.min(1440, Math.max(1, Math.ceil((next.getTime() - now.getTime()) / 60000)))
  return { minutes, tomorrow }
}

type Note = { kind: 'saved' | 'error'; text: string }

/** Shared "saving / Saved / error" bookkeeping, keyed by control. */
function useSaver() {
  const [busy, setBusy] = useState<Set<string>>(new Set())
  const [notes, setNotes] = useState<Record<string, Note>>({})
  const timers = useRef<number[]>([])
  useEffect(() => () => timers.current.forEach(window.clearTimeout), [])

  async function run(key: string, work: () => Promise<unknown>, opts: { quiet?: boolean } = {}): Promise<boolean> {
    setBusy((s) => new Set(s).add(key))
    setNotes((n) => {
      const rest = { ...n }
      delete rest[key]
      return rest
    })
    try {
      await work()
      if (!opts.quiet) {
        setNotes((n) => ({ ...n, [key]: { kind: 'saved', text: 'Saved' } }))
        timers.current.push(
          window.setTimeout(
            () =>
              setNotes((n) => {
                if (n[key]?.kind !== 'saved') return n
                const rest = { ...n }
                delete rest[key]
                return rest
              }),
            2500,
          ),
        )
      }
      return true
    } catch (e) {
      setNotes((n) => ({ ...n, [key]: { kind: 'error', text: errText(e) } }))
      return false
    } finally {
      setBusy((s) => {
        const n = new Set(s)
        n.delete(key)
        return n
      })
    }
  }
  return { busy, notes, run }
}

function NoteText({ note }: { note?: Note }) {
  if (!note) return null
  return (
    <span className="rl-note" data-kind={note.kind} role={note.kind === 'error' ? 'alert' : 'status'}>
      {note.text}
    </span>
  )
}

function Skeletons() {
  return (
    <div className="rl-stack" aria-busy="true" aria-label="Loading rules">
      <div className="skeleton" style={{ height: 190 }} />
      <div className="skeleton" style={{ height: 90 }} />
      <div className="skeleton" style={{ height: 340 }} />
      <div className="skeleton" style={{ height: 200 }} />
    </div>
  )
}

// ---------------------------------------------------------------- Pause internet

type Target = { id: number | null; label: string }

function PausePanel({
  targets, pauses, nowIso, saver, onChanged,
}: {
  targets: Target[]; pauses: PauseRow[]; nowIso: string
  saver: ReturnType<typeof useSaver>; onChanged: () => Promise<unknown>
}) {
  const [choice, setChoice] = useState<Record<string, string>>({})
  const seven = minutesToSeven(nowIso)
  const options = [
    { value: '15', label: '15 min', minutes: 15 },
    { value: '30', label: '30 min', minutes: 30 },
    { value: '60', label: '1 hour', minutes: 60 },
    { value: '120', label: '2 hours', minutes: 120 },
    { value: 'seven', label: seven.tomorrow ? 'Until tomorrow 07:00' : 'Until 07:00', minutes: seven.minutes },
  ]
  const homePause = pauses.find((p) => p.child_id === null)
  const nowDate = nowIso.slice(0, 10)

  const until = (p: PauseRow) => `${clock(p.until_ts)}${p.until_ts.slice(0, 10) !== nowDate ? ' tomorrow' : ''}`

  return (
    <section className="panel" aria-labelledby="rl-pause-h">
      <div className="panel-head">
        <h2 id="rl-pause-h">Pause internet</h2>
      </div>
      <ul className="rl-pause-list">
        {targets.map((t) => {
          const key = `pause-${targetKey(t.id)}`
          const own = pauses.find((p) => p.child_id === t.id)
          const withHome = t.id !== null && !own && homePause
          const sel = choice[targetKey(t.id)] ?? '30'
          const busy = saver.busy.has(key)
          return (
            <li key={key} className="rl-pause-row">
              <div className="rl-pause-who">
                <strong>{t.label}</strong>
                {own && <span className="badge badge-block">Paused until {until(own)}</span>}
                {withHome && <span className="badge badge-block">Paused with the whole home until {until(homePause)}</span>}
              </div>
              <div className="rl-pause-actions">
                {own ? (
                  <button
                    type="button" className="btn btn-secondary" disabled={busy}
                    onClick={() => saver.run(key, async () => { await post('/resume', { child_id: t.id }); await onChanged() }, { quiet: true })}
                  >
                    <Play aria-hidden="true" /> Resume now
                  </button>
                ) : (
                  <>
                    <label className="rl-visually-hidden" htmlFor={`dur-${key}`}>Pause length for {t.label}</label>
                    <select
                      id={`dur-${key}`} className="select rl-dur" value={sel} disabled={busy}
                      onChange={(e) => setChoice((c) => ({ ...c, [targetKey(t.id)]: e.target.value }))}
                    >
                      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                    <button
                      type="button" className="btn btn-primary" disabled={busy}
                      onClick={() => {
                        const m = options.find((o) => o.value === sel)?.minutes ?? 30
                        saver.run(key, async () => { await post('/pause', { child_id: t.id, minutes: m }); await onChanged() }, { quiet: true })
                      }}
                    >
                      <Pause aria-hidden="true" /> Pause internet
                    </button>
                  </>
                )}
              </div>
              <NoteText note={saver.notes[key]} />
            </li>
          )
        })}
      </ul>
      <p className="rl-foot">
        Pausing blocks every site for that child's devices, or for the whole home. Background system traffic (time sync, update checks) keeps working.
      </p>
    </section>
  )
}

// ---------------------------------------------------------------- Always blocked

function AlwaysBlocked() {
  return (
    <section className="panel" aria-labelledby="rl-always-h">
      <div className="panel-head">
        <h2 id="rl-always-h">Always blocked</h2>
        <span className="rl-muted">Cannot be changed</span>
      </div>
      <ul className="rl-always">
        <li>
          <Lock aria-hidden="true" />
          <div>
            <strong>Explicit sites</strong>
            <p>Blocked for every device in the home, so there is nothing to switch on or off.</p>
          </div>
        </li>
        <li>
          <Lock aria-hidden="true" />
          <div>
            <strong>Encrypted DNS servers</strong>
            <p>Encrypted DNS would hide lookups from the filter, so these servers are blocked for everyone.</p>
          </div>
        </li>
      </ul>
    </section>
  )
}

// ---------------------------------------------------------------- Category matrix

type Cell = 'inherit' | 'block' | 'allow'

function Matrix({
  categories, rules, kids, saver, onChanged,
}: {
  categories: string[]; rules: RuleRow[]; kids: Child[]
  saver: ReturnType<typeof useSaver>; onChanged: () => Promise<unknown>
}) {
  const [col, setCol] = useState<string>('home')
  const cols: Target[] = [{ id: null, label: 'Whole home' }, ...kids.map((k) => ({ id: k.id, label: k.name }))]
  const valueOf = (childId: number | null, cat: string): Cell =>
    rules.find((r) => r.child_id === childId && r.category === cat)?.action ?? 'inherit'
  const homeAction = (cat: string) => (valueOf(null, cat) === 'block' ? 'blocked' : 'allowed')

  function change(t: Target, cat: string, v: Cell) {
    const key = `rule-${targetKey(t.id)}-${cat}`
    saver.run(key, async () => {
      await put('/rules', { child_id: t.id, category: cat, action: v === 'inherit' ? null : v })
      await onChanged()
    })
  }

  return (
    <section className="panel" aria-labelledby="rl-cat-h">
      <div className="panel-head">
        <h2 id="rl-cat-h">Blocked categories</h2>
      </div>
      <div className="rl-cat-intro">
        <p>
          A rule for a child wins over the rule for the whole home. "Same as home" means the child follows the home column.
          Pauses and bedtimes are checked first and block everything while they last.
        </p>
        <div className="rl-switch" role="group" aria-label="Show column">
          {cols.map((c) => (
            <button
              key={targetKey(c.id)} type="button" className="rl-switch-btn"
              aria-pressed={col === targetKey(c.id)} onClick={() => setCol(targetKey(c.id))}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>
      <div className="table-wrap">
        <table className="table rl-matrix">
          <thead>
            <tr>
              <th scope="col">Category</th>
              {cols.map((c) => <th key={targetKey(c.id)} scope="col" data-on={col === targetKey(c.id)}>{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <tr key={cat}>
                <th scope="row" className="rl-cat-name">
                  {categoryLabel(cat)}
                  {cat === 'payments' && (
                    <span className="rl-cat-hint">
                      For children, store and payment sites always wait for your OK (see Payments), whatever is set here.
                    </span>
                  )}
                </th>
                {cols.map((c) => {
                  const key = `rule-${targetKey(c.id)}-${cat}`
                  const v = valueOf(c.id, cat)
                  const payChild = cat === 'payments' && c.id !== null
                  const label = `${categoryLabel(cat)} for ${c.label}`
                  return (
                    <td key={targetKey(c.id)} data-on={col === targetKey(c.id)}>
                      {payChild ? (
                        <span className="badge badge-warn">Waits for your OK</span>
                      ) : (
                        <div className="rl-cell">
                          <select
                            className="select rl-select" data-state={v === 'inherit' ? homeAction(cat) : v === 'block' ? 'blocked' : 'allowed'}
                            aria-label={label} value={v} disabled={saver.busy.has(key)}
                            onChange={(e) => change(c, cat, e.target.value as Cell)}
                          >
                            {c.id !== null && <option value="inherit">Same as home ({homeAction(cat)})</option>}
                            <option value="allow">Allowed</option>
                            <option value="block">Blocked</option>
                          </select>
                          <NoteText note={saver.notes[key]} />
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rl-foot">
        Not listed: background system traffic is always allowed, and explicit sites and encrypted DNS are always blocked.
      </p>
    </section>
  )
}

// ---------------------------------------------------------------- Schedules

type FormValues = { child_id: number; name: string; days: string[]; start: string; end: string }

function ScheduleForm({
  kids, initial, editing, onCancel, onSubmit, busy, error,
}: {
  kids: Child[]; initial: FormValues; editing: boolean; busy: boolean; error?: string
  onCancel: () => void; onSubmit: (v: FormValues) => void
}) {
  const [v, setV] = useState<FormValues>(initial)
  const [local, setLocal] = useState<string | null>(null)
  const uid = `sf-${editing ? 'e' : 'n'}-${initial.child_id}-${initial.name.length}`
  const toggle = (d: string) =>
    setV((x) => ({ ...x, days: x.days.includes(d) ? x.days.filter((y) => y !== d) : [...x.days, d] }))

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!v.name.trim()) return setLocal('Give the schedule a name, for example "School nights".')
    if (v.days.length === 0) return setLocal('Pick at least one day.')
    if (!v.start || !v.end) return setLocal('Pick a start and an end time.')
    if (v.start === v.end) return setLocal('Start and end must be different times.')
    setLocal(null)
    onSubmit({ ...v, name: v.name.trim() })
  }
  const shown = local ?? error

  return (
    <form className="rl-form" onSubmit={submit} noValidate>
      <div className="rl-form-grid">
        {!editing && (
          <div className="field">
            <label htmlFor={`${uid}-child`}>Child</label>
            <select id={`${uid}-child`} className="select" value={v.child_id} disabled={busy}
              onChange={(e) => setV({ ...v, child_id: Number(e.target.value) })}>
              {kids.map((k) => <option key={k.id} value={k.id}>{k.name}</option>)}
            </select>
          </div>
        )}
        <div className="field">
          <label htmlFor={`${uid}-name`}>Name</label>
          <input id={`${uid}-name`} className="input" value={v.name} maxLength={60} disabled={busy}
            placeholder="School nights" aria-invalid={!!shown && !v.name.trim()}
            onChange={(e) => setV({ ...v, name: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor={`${uid}-start`}>Internet off from</label>
          <input id={`${uid}-start`} className="input" type="time" value={v.start} disabled={busy}
            onChange={(e) => setV({ ...v, start: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor={`${uid}-end`}>Back on at</label>
          <input id={`${uid}-end`} className="input" type="time" value={v.end} disabled={busy}
            onChange={(e) => setV({ ...v, end: e.target.value })} />
        </div>
      </div>
      <fieldset className="rl-days" disabled={busy}>
        <legend>Days it starts on</legend>
        <div className="rl-chips">
          {DAYS.map((d) => (
            <button key={d} type="button" className="rl-chip rl-chip-toggle" aria-pressed={v.days.includes(d)} onClick={() => toggle(d)}>
              {DAY_SHORT[d]}
            </button>
          ))}
        </div>
      </fieldset>
      <p className="rl-muted rl-cross">A schedule that crosses midnight, like 22:00-06:30, is set on the day it starts.</p>
      {shown && (
        <div className="callout callout-error" role="alert">
          <AlertTriangle aria-hidden="true" />
          <span>{shown}</span>
        </div>
      )}
      <div className="rl-form-actions">
        <button type="submit" className="btn btn-primary" disabled={busy}>{editing ? 'Save schedule' : 'Add schedule'}</button>
        <button type="button" className="btn btn-ghost" disabled={busy} onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

function Schedules({
  kids, schedules, saver, onChanged,
}: {
  kids: Child[]; schedules: Schedule[]
  saver: ReturnType<typeof useSaver>; onChanged: () => Promise<unknown>
}) {
  const [editing, setEditing] = useState<number | null>(null)
  const [adding, setAdding] = useState(false)
  const [confirmDel, setConfirmDel] = useState<number | null>(null)
  const addKey = 'sched-add'

  const toForm = (s: Schedule): FormValues => ({
    child_id: s.child_id, name: s.name, days: s.days.split(',').filter(Boolean), start: s.start, end: s.end,
  })
  const ordered = (ids: string[]) => DAYS.filter((d) => ids.includes(d)).join(',')

  return (
    <section className="panel" aria-labelledby="rl-sched-h">
      <div className="panel-head">
        <h2 id="rl-sched-h">Internet schedules</h2>
        {!adding && kids.length > 0 && (
          <button type="button" className="btn btn-secondary" onClick={() => { setAdding(true); setEditing(null) }}>
            <Plus aria-hidden="true" /> Add schedule
          </button>
        )}
      </div>
      <div className="rl-sched-body">
        <p className="rl-muted">
          During a schedule the internet is off for that child's devices. A schedule that crosses midnight, like 22:00-06:30, is set on the day it starts.
        </p>
        {adding && (
          <div className="rl-sched-add">
            <h3>New schedule</h3>
            <ScheduleForm
              kids={kids} editing={false} busy={saver.busy.has(addKey)} error={saver.notes[addKey]?.kind === 'error' ? saver.notes[addKey].text : undefined}
              initial={{ child_id: kids[0].id, name: '', days: ['sun', 'mon', 'tue', 'wed', 'thu'], start: '21:00', end: '07:00' }}
              onCancel={() => setAdding(false)}
              onSubmit={async (v) => {
                const ok = await saver.run(addKey, async () => {
                  await post('/schedules', { child_id: v.child_id, name: v.name, days: ordered(v.days), start: v.start, end: v.end })
                  await onChanged()
                }, { quiet: true })
                if (ok) setAdding(false)
              }}
            />
          </div>
        )}
        {kids.map((k) => {
          const mine = schedules.filter((s) => s.child_id === k.id)
          return (
            <div key={k.id} className="rl-child-block">
              <h3>{k.name}</h3>
              {mine.length === 0 ? (
                <p className="rl-muted">No schedules. {k.name} can use the internet at any hour. Use "Add schedule" to set a bedtime.</p>
              ) : (
                <ul className="rl-sched-list">
                  {mine.map((s) => {
                    const key = `sched-${s.id}`
                    const busy = saver.busy.has(key)
                    const err = saver.notes[key]?.kind === 'error' ? saver.notes[key].text : undefined
                    if (editing === s.id) {
                      return (
                        <li key={s.id} className="rl-sched">
                          <ScheduleForm
                            kids={kids} editing busy={busy} error={err} initial={toForm(s)}
                            onCancel={() => setEditing(null)}
                            onSubmit={async (v) => {
                              const ok = await saver.run(key, async () => {
                                await patch(`/schedules/${s.id}`, { name: v.name, days: ordered(v.days), start: v.start, end: v.end })
                                await onChanged()
                              }, { quiet: true })
                              if (ok) setEditing(null)
                            }}
                          />
                        </li>
                      )
                    }
                    return (
                      <li key={s.id} className="rl-sched" data-off={!s.enabled}>
                        <div className="rl-sched-main">
                          <strong>{s.name}</strong>
                          <span className="rl-time mono">{s.start}-{s.end}</span>
                          <span className="rl-chips" aria-label={`Days: ${s.days}`}>
                            {s.days.split(',').filter(Boolean).map((d) => <span key={d} className="rl-chip">{DAY_SHORT[d] ?? d}</span>)}
                          </span>
                        </div>
                        {confirmDel === s.id ? (
                          <div className="rl-sched-actions" role="group" aria-label="Confirm delete">
                            <span className="rl-confirm">Delete this schedule?</span>
                            <button type="button" className="btn btn-danger" disabled={busy}
                              onClick={async () => {
                                const ok = await saver.run(key, async () => { await del(`/schedules/${s.id}`); await onChanged() }, { quiet: true })
                                if (ok) setConfirmDel(null)
                              }}>
                              <Trash2 aria-hidden="true" /> Delete
                            </button>
                            <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => setConfirmDel(null)}>
                              <X aria-hidden="true" /> Keep it
                            </button>
                          </div>
                        ) : (
                          <div className="rl-sched-actions">
                            <label className="check rl-toggle">
                              <input type="checkbox" checked={s.enabled} disabled={busy}
                                onChange={(e) => saver.run(key, async () => { await patch(`/schedules/${s.id}`, { enabled: e.target.checked }); await onChanged() })} />
                              <span>{s.enabled ? 'On' : 'Off'}</span>
                            </label>
                            <button type="button" className="btn btn-ghost" disabled={busy}
                              onClick={() => { setEditing(s.id); setAdding(false); setConfirmDel(null) }}>
                              <Pencil aria-hidden="true" /> Edit
                            </button>
                            <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => setConfirmDel(s.id)}>
                              <Trash2 aria-hidden="true" /> Delete
                            </button>
                          </div>
                        )}
                        <NoteText note={saver.notes[key]} />
                        {err && editing !== s.id && <span className="rl-note" data-kind="error" role="alert">{err}</span>}
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

// ---------------------------------------------------------------- Screen

export default function Rules() {
  const { title, what } = SCREEN_INFO.rules
  const ov = usePoll<{ now: string }>('/overview')
  const kidsQ = usePoll<{ items: Child[] }>('/children', 0)
  const rulesQ = usePoll<RulesData>('/rules', 0)
  const schedQ = usePoll<{ items: Schedule[] }>('/schedules', 0)
  const pauseQ = usePoll<{ items: PauseRow[] }>('/pauses')
  const saver = useSaver()

  const reloadAll = () => Promise.all([rulesQ.reload(), schedQ.reload(), pauseQ.reload(), ov.reload()])
  const reloadPauses = () => Promise.all([pauseQ.reload(), ov.reload()])

  const error = kidsQ.error ?? rulesQ.error ?? schedQ.error ?? pauseQ.error ?? ov.error
  const ready = kidsQ.data && rulesQ.data && schedQ.data && pauseQ.data && ov.data

  const kids = kidsQ.data?.items ?? []
  const categories = (rulesQ.data?.categories ?? []).filter((c) => !c.fixed && !HIDDEN_CATEGORIES.has(c.name)).map((c) => c.name)
  const targets: Target[] = [{ id: null, label: 'Whole home' }, ...kids.map((k) => ({ id: k.id, label: k.name }))]

  return (
    <div className="page rl-page">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>{what}</p>
        </div>
      </div>

      {error && !ready ? (
        <div className="callout callout-error" role="alert">
          <AlertTriangle aria-hidden="true" />
          <div className="rl-err">
            <span>{error}</span>
            <button type="button" className="btn btn-secondary" onClick={() => { kidsQ.reload(); rulesQ.reload(); schedQ.reload(); pauseQ.reload(); ov.reload() }}>
              Try again
            </button>
          </div>
        </div>
      ) : !ready ? (
        <Skeletons />
      ) : (
        <div className="rl-stack">
          {error && (
            <div className="callout callout-warn" role="status">
              <AlertTriangle aria-hidden="true" />
              <span>Some data could not be refreshed: {error}</span>
            </div>
          )}
          <PausePanel targets={targets} pauses={pauseQ.data!.items} nowIso={ov.data!.now} saver={saver} onChanged={reloadPauses} />
          <AlwaysBlocked />
          <Matrix categories={categories} rules={rulesQ.data!.rules} kids={kids} saver={saver} onChanged={reloadAll} />
          <Schedules kids={kids} schedules={schedQ.data!.items} saver={saver} onChanged={reloadAll} />
          <p className="rl-footnote">
            <Info aria-hidden="true" />
            <span>Changes apply to the next site a device asks for. Watch it happen in <a href="#/activity">Live activity</a>.</span>
          </p>
        </div>
      )}
    </div>
  )
}
