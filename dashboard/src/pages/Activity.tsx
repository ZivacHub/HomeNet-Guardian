import { AlertTriangle, ArrowUp, Pause, Play, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Domain } from '../components/Domain'
import { get } from '../lib/api'
import { categoryLabel, clock } from '../lib/format'
import { usePoll } from '../lib/usePoll'
import '../styles/pages/activity.css'
import { SCREEN_INFO } from './screenInfo'

type Lookup = {
  id: number
  ts: string
  device_id: number
  domain: string
  source: string
  category: string
  decision: 'allowed' | 'blocked'
  reason: string
  device_name: string
  child_id: number | null
}
type Page = { items: Lookup[]; next_before_id: number | null }
type Filters = { device: string; child: string; decision: '' | 'allowed' | 'blocked'; category: string; q: string }

const EMPTY: Filters = { device: '', child: '', decision: '', category: '', q: '' }
const LIMIT = 100
const POLL_MS = 5000
const SOURCE_HELP =
  'DNS: the device asked the router for the site’s address. SNI: the site name visible at the start of an encrypted connection.'

/** Filters live in the hash query (#/activity?decision=blocked&device=4) so other screens can link here pre-filtered. */
function readHash(): Filters {
  const hash = window.location.hash.replace(/^#\/?/, '')
  const [id, query = ''] = hash.split('?')
  if (id !== 'activity') return EMPTY
  const p = new URLSearchParams(query)
  const decision = p.get('decision')
  return {
    device: p.get('device') ?? '',
    child: p.get('child') ?? '',
    decision: decision === 'allowed' || decision === 'blocked' ? decision : '',
    category: p.get('category') ?? '',
    q: p.get('q') ?? '',
  }
}

function writeHash(f: Filters) {
  const p = new URLSearchParams()
  if (f.device) p.set('device', f.device)
  if (f.child) p.set('child', f.child)
  if (f.decision) p.set('decision', f.decision)
  if (f.category) p.set('category', f.category)
  if (f.q) p.set('q', f.q)
  const qs = p.toString()
  const next = `#/activity${qs ? `?${qs}` : ''}`
  if (window.location.hash !== next) window.history.replaceState(null, '', next)
}

function apiPath(f: Filters, beforeId?: number) {
  const p = new URLSearchParams({ limit: String(LIMIT) })
  if (f.device) p.set('device_id', f.device)
  if (f.child) p.set('child_id', f.child)
  if (f.decision) p.set('decision', f.decision)
  if (f.category) p.set('category', f.category)
  if (f.q) p.set('q', f.q)
  if (beforeId !== undefined) p.set('before_id', String(beforeId))
  return `/activity?${p.toString()}`
}

const sameFilters = (a: Filters, b: Filters) =>
  a.device === b.device && a.child === b.child && a.decision === b.decision && a.category === b.category && a.q === b.q

export default function Activity() {
  const info = SCREEN_INFO.activity
  const [filters, setFilters] = useState<Filters>(readHash)
  const [qInput, setQInput] = useState(filters.q)
  const [live, setLive] = useState(true)

  const [rows, setRows] = useState<Lookup[] | null>(null)
  const [next, setNext] = useState<number | null>(null)
  const [pending, setPending] = useState<Lookup[]>([])
  const [fresh, setFresh] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [scrolled, setScrolled] = useState(false)
  const [moreBusy, setMoreBusy] = useState(false)

  const rowsRef = useRef<Lookup[] | null>(null)
  const pendingRef = useRef<Lookup[]>([])
  const scrolledRef = useRef(false)
  const gen = useRef(0)
  const filtersRef = useRef(filters)
  const scroller = useRef<HTMLDivElement>(null)

  const devices = usePoll<{ items: { id: number; display_name: string }[] }>('/devices', 0)
  const children = usePoll<{ items: { id: number; name: string }[] }>('/children', 0)
  const meta = usePoll<{ categories: { name: string }[] }>('/meta', 0)

  const commitRows = (v: Lookup[] | null) => {
    rowsRef.current = v
    setRows(v)
  }
  const commitPending = (v: Lookup[]) => {
    pendingRef.current = v
    setPending(v)
  }

  // Filters -> URL, and URL -> filters when a link from another screen changes the hash.
  useEffect(() => {
    filtersRef.current = filters
    writeHash(filters)
  }, [filters])
  useEffect(() => {
    const on = () => {
      if (!window.location.hash.replace(/^#\/?/, '').startsWith('activity')) return
      const f = readHash()
      if (!sameFilters(f, filtersRef.current)) {
        setFilters(f)
        setQInput(f.q)
      }
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])

  // Debounced search box.
  useEffect(() => {
    if (qInput.trim() === filters.q) return
    const t = window.setTimeout(() => setFilters((f) => ({ ...f, q: qInput.trim() })), 300)
    return () => window.clearTimeout(t)
  }, [qInput, filters.q])

  const markFresh = (items: Lookup[]) => {
    const ids = items.map((i) => i.id)
    setFresh((s) => new Set([...s, ...ids]))
    window.setTimeout(
      () =>
        setFresh((s) => {
          const n = new Set(s)
          ids.forEach((i) => n.delete(i))
          return n
        }),
      1500,
    )
  }

  const load = useCallback(async () => {
    const g = gen.current
    try {
      const res = await get<Page>(apiPath(filtersRef.current))
      if (g !== gen.current) return
      setError(null)
      const current = rowsRef.current
      if (current === null) {
        commitRows(res.items)
        setNext(res.next_before_id)
        return
      }
      const top = current[0]?.id ?? 0
      const newer = res.items.filter((i) => i.id > top)
      if (newer.length === 0) return
      if (scrolledRef.current) {
        commitPending(newer)
      } else {
        commitRows([...newer, ...current])
        markFresh(newer)
      }
    } catch (e) {
      if (g === gen.current) setError(e instanceof Error ? e.message : 'The server could not be reached.')
    }
  }, [])

  // New filters: start over with a fresh first page.
  useEffect(() => {
    gen.current += 1
    commitRows(null)
    commitPending([])
    setNext(null)
    setError(null)
    scrolledRef.current = false
    setScrolled(false)
    if (scroller.current) scroller.current.scrollTop = 0
    load()
  }, [filters, load])

  // Poll while live.
  useEffect(() => {
    if (!live) return
    const t = window.setInterval(load, POLL_MS)
    return () => window.clearInterval(t)
  }, [live, load])

  const flush = () => {
    const p = pendingRef.current
    if (p.length === 0) return
    commitPending([])
    commitRows([...p, ...(rowsRef.current ?? [])])
    markFresh(p)
  }

  const onScroll = () => {
    const top = (scroller.current?.scrollTop ?? 0) <= 8
    if (top === !scrolledRef.current) return
    scrolledRef.current = !top
    setScrolled(!top)
    if (top) flush()
  }

  const jumpToTop = () => {
    scroller.current?.scrollTo({ top: 0 })
    scrolledRef.current = false
    setScrolled(false)
    flush()
  }

  const loadOlder = async () => {
    if (next === null || moreBusy) return
    setMoreBusy(true)
    const g = gen.current
    try {
      const res = await get<Page>(apiPath(filtersRef.current, next))
      if (g !== gen.current) return
      const have = new Set((rowsRef.current ?? []).map((r) => r.id))
      commitRows([...(rowsRef.current ?? []), ...res.items.filter((i) => !have.has(i.id))])
      setNext(res.next_before_id)
    } catch (e) {
      if (g === gen.current) setError(e instanceof Error ? e.message : 'The server could not be reached.')
    } finally {
      setMoreBusy(false)
    }
  }

  const resume = () => {
    setLive(true)
    load()
  }

  const anyFilter = useMemo(() => !sameFilters(filters, EMPTY), [filters])
  const clear = () => {
    setQInput('')
    setFilters(EMPTY)
  }
  const set = <K extends keyof Filters>(k: K, v: Filters[K]) => setFilters((f) => ({ ...f, [k]: v }))

  const results: { value: Filters['decision']; label: string }[] = [
    { value: '', label: 'All' },
    { value: 'allowed', label: 'Allowed' },
    { value: 'blocked', label: 'Blocked' },
  ]

  return (
    <div className="page activity">
      <div className="page-head">
        <div>
          <h1>{info.title}</h1>
          <p>{info.what} New lookups arrive every few seconds.</p>
        </div>
        <div className="act-live">
          <span className={`act-status ${live ? 'is-live' : ''}`} role="status">
            <span className="act-dot" aria-hidden="true" />
            {live ? 'Live · updates every 5 s' : 'Paused'}
          </span>
          {live ? (
            <button className="btn btn-secondary" onClick={() => setLive(false)}>
              <Pause /> Pause updates
            </button>
          ) : (
            <button className="btn btn-primary" onClick={resume}>
              <Play /> Resume updates
            </button>
          )}
        </div>
      </div>

      <div className="act-filters">
        <div className="field">
          <label htmlFor="act-device">Device</label>
          <select id="act-device" className="select" value={filters.device} onChange={(e) => set('device', e.target.value)}>
            <option value="">All devices</option>
            {devices.data?.items.map((d) => (
              <option key={d.id} value={d.id}>
                {d.display_name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="act-child">Child</label>
          <select id="act-child" className="select" value={filters.child} onChange={(e) => set('child', e.target.value)}>
            <option value="">All children</option>
            {children.data?.items.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <span className="act-label" id="act-result-label">
            Result
          </span>
          <div className="act-seg" role="group" aria-labelledby="act-result-label">
            {results.map((r) => (
              <button
                key={r.value}
                type="button"
                aria-pressed={filters.decision === r.value}
                className={filters.decision === r.value ? 'is-on' : ''}
                onClick={() => set('decision', r.value)}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
        <div className="field">
          <label htmlFor="act-cat">Category</label>
          <select id="act-cat" className="select" value={filters.category} onChange={(e) => set('category', e.target.value)}>
            <option value="">All categories</option>
            {meta.data?.categories.map((c) => (
              <option key={c.name} value={c.name}>
                {categoryLabel(c.name)}
              </option>
            ))}
          </select>
        </div>
        <div className="field act-search">
          <label htmlFor="act-q">Search site</label>
          <input
            id="act-q"
            className="input"
            type="search"
            value={qInput}
            placeholder="Search a site name, e.g. youtube"
            onChange={(e) => setQInput(e.target.value)}
          />
        </div>
        {anyFilter && (
          <button className="btn btn-ghost act-clear" onClick={clear}>
            <X /> Clear filters
          </button>
        )}
      </div>

      {error && rows !== null && (
        <div className="callout callout-error act-note" role="alert">
          <AlertTriangle aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      <div className="panel act-panel">
        {error && rows === null ? (
          <div className="act-state">
            <div className="callout callout-error" role="alert">
              <AlertTriangle aria-hidden="true" />
              <span>{error}</span>
            </div>
            <button className="btn btn-secondary" onClick={load}>
              Try again
            </button>
          </div>
        ) : rows !== null && rows.length === 0 ? (
          <div className="empty">
            <h2>No lookups match these filters.</h2>
            <p>{anyFilter ? 'Try a different site name, or show everything again.' : 'Nothing has been looked up yet today.'}</p>
            {anyFilter && (
              <button className="btn btn-secondary act-empty-btn" onClick={clear}>
                <X /> Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="table-wrap act-scroll" ref={scroller} onScroll={onScroll}>
            {scrolled && pending.length > 0 && (
              <button className="btn btn-primary act-jump" onClick={jumpToTop}>
                <ArrowUp /> {pending.length} new {'—'} jump to top
              </button>
            )}
            <table className="table act-table">
              <thead>
                <tr>
                  <th className="act-c-time">Time</th>
                  <th>Device</th>
                  <th>Site</th>
                  <th>Category</th>
                  <th>Seen via</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {rows === null
                  ? Array.from({ length: 10 }, (_, i) => (
                      <tr key={i} aria-hidden="true">
                        {[60, 90, 150, 90, 80, 120].map((w, j) => (
                          <td key={j}>
                            <div className="skeleton act-skel" style={{ width: w }} />
                          </td>
                        ))}
                      </tr>
                    ))
                  : rows.map((r) => (
                      <tr key={r.id} className={`${r.decision === 'blocked' ? 'is-blocked' : ''} ${fresh.has(r.id) ? 'is-new' : ''}`}>
                        <td className="mono num act-c-time">{clock(r.ts, true)}</td>
                        <td>{r.device_name}</td>
                        <td>
                          <Domain domain={r.domain} category={r.category} />
                        </td>
                        <td className="act-muted">{categoryLabel(r.category)}</td>
                        <td>
                          <span className="badge badge-plain" title={SOURCE_HELP}>
                            {r.source === 'sni' ? 'Encrypted name (SNI)' : 'DNS lookup'}
                          </span>
                        </td>
                        <td>
                          <div className="act-result">
                            <span className={`badge ${r.decision === 'blocked' ? 'badge-block' : 'badge-ok'}`}>
                              {r.decision === 'blocked' ? 'Blocked' : 'Allowed'}
                            </span>
                            <span className="act-reason">{r.reason}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}

        {rows !== null && rows.length > 0 && (
          <div className="act-foot">
            <span className="act-muted num">
              {next === null ? `Showing all ${rows.length} lookups` : `Showing ${rows.length} lookups`}
            </span>
            {next !== null && (
              <button className="btn btn-secondary" onClick={loadOlder} disabled={moreBusy}>
                {moreBusy ? 'Loading…' : 'Load older'}
              </button>
            )}
          </div>
        )}
      </div>

      <p className="act-footnote">
        Only site names are visible, never what is on the page. See <a href="#/settings">Settings {'→'} What this does not see</a>.
      </p>
    </div>
  )
}
