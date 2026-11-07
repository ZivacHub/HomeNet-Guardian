import { useMemo, useState } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { categoryLabel, minutes } from '../lib/format'
import { usePoll } from '../lib/usePoll'
import { SCREEN_INFO } from './screenInfo'
import '../styles/pages/time.css'

type Child = { id: number; name: string }
type Meta = { today: string; estimate_note: string }
type TimeUse = {
  child_id: number; date: string; total_minutes: number
  by_category: Record<string, number>; by_site: Record<string, number>
  by_hour: number[]; sessions: number; note: string
}

// One fixed colour per category, the same on every chart. Slots follow the dataviz categorical order;
// categories beyond the eight hues share the muted "other" colour and are always labelled in words.
const CAT_SLOT: Record<string, number> = {
  social: 1, video: 2, games: 7, learning: 6, messaging: 3, music: 5, search: 4, shopping: 8,
}
const catColor = (c: string) => `var(--viz-${CAT_SLOT[c] ?? 0})`

const pad = (n: number) => String(n).padStart(2, '0')

/** The last 7 days (today first) as ISO dates, computed from the simulated "today". */
function lastDays(today: string): { value: string; label: string }[] {
  const [y, m, d] = today.split('-').map(Number)
  return Array.from({ length: 7 }, (_, i) => {
    const dt = new Date(y, m - 1, d - i, 12)
    const value = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`
    const text = dt.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
    return { value, label: i === 0 ? 'Today' : i === 1 ? 'Yesterday' : text }
  })
}

function dayWords(i: number, label: string) {
  return i === 0 ? 'today' : i === 1 ? 'yesterday' : `on ${label}`
}

function HourTip({ active, payload }: { active?: boolean; payload?: { payload: { h: number; min: number } }[] }) {
  if (!active || !payload?.length) return null
  const { h, min } = payload[0].payload
  return (
    <div className="time-tip">
      <span className="num">{pad(h)}:00-{pad((h + 1) % 24)}:00</span> · <span className="num">{Math.round(min)} min</span> (estimate)
    </div>
  )
}

export default function Time() {
  const { title, what } = SCREEN_INFO.time
  const kids = usePoll<{ items: Child[] }>('/children', 0)
  const meta = usePoll<Meta>('/meta', 0)
  const [childPick, setChildPick] = useState<number | null>(null)
  const [dayPick, setDayPick] = useState<string | null>(null)
  const [showSites, setShowSites] = useState(false)

  const children = kids.data?.items ?? []
  const child = children.find((c) => c.id === childPick) ?? children[0] ?? null
  const days = useMemo(() => (meta.data ? lastDays(meta.data.today) : []), [meta.data])
  const dayIdx = Math.max(0, days.findIndex((d) => d.value === dayPick))
  const day = days[dayIdx] ?? null

  const path = child && day ? `/timeuse?child_id=${child.id}&date=${day.value}` : null
  const tu = usePoll<TimeUse>(path, 30000)
  const fresh = tu.data && child && day && tu.data.child_id === child.id && tu.data.date === day.value ? tu.data : null

  const setupError = kids.error || meta.error
  const error = setupError ?? (tu.error && !fresh ? tu.error : null)
  const retry = () => { kids.reload(); meta.reload(); tu.reload() }
  const loading = !error && (!fresh || kids.loading || meta.loading)

  const cats = useMemo(
    () => Object.entries(fresh?.by_category ?? {}).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]),
    [fresh],
  )
  const sites = useMemo(
    () => Object.entries(fresh?.by_site ?? {}).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]).slice(0, 10),
    [fresh],
  )
  const hours = useMemo(
    () => (fresh?.by_hour ?? []).map((min, h) => ({ h, label: pad(h), min })),
    [fresh],
  )
  const empty = !!fresh && (fresh.total_minutes <= 0 || cats.length === 0)
  const hasExplicit = (fresh?.by_category.explicit ?? 0) > 0
  const maxCat = cats[0]?.[1] ?? 1
  const maxSite = sites[0]?.[1] ?? 1
  const peak = hours.reduce((a, b) => (b.min > a.min ? b : a), { h: 0, label: '00', min: 0 })
  const name = child?.name ?? ''

  return (
    <div className="page time-page">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>{what}</p>
        </div>
        <div className="time-controls">
          {children.length > 0 && (
            <div className="seg" role="radiogroup" aria-label="Child">
              {children.map((c) => (
                <button
                  key={c.id} type="button" role="radio" aria-checked={child?.id === c.id}
                  className={child?.id === c.id ? 'seg-on' : ''}
                  onClick={() => setChildPick(c.id)}
                >
                  {c.name}
                </button>
              ))}
            </div>
          )}
          {days.length > 0 && (
            <div className="field">
              <label htmlFor="time-day" className="time-vh">Day</label>
              <select id="time-day" className="select time-day" value={day?.value} onChange={(e) => setDayPick(e.target.value)}>
                {days.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="callout callout-error" role="alert">
          <AlertTriangle aria-hidden />
          <div className="time-err">
            <span>{error}</span>
            <button className="btn btn-secondary" onClick={retry}><RefreshCw aria-hidden /> Try again</button>
          </div>
        </div>
      )}

      {loading && (
        <div className="time-grid" aria-busy="true" aria-label="Loading">
          <div className="skeleton time-sk-sum" />
          <div className="skeleton time-sk-chart" />
          <div className="skeleton time-sk-chart" />
          <div className="skeleton time-sk-list" />
        </div>
      )}

      {fresh && !error && (
        <div className="time-grid">
          {empty ? (
            <section className="panel time-full">
              <div className="empty">
                <h2>Nothing to show for this day</h2>
                <p>No lookups were recorded for {name} on this day.</p>
                <p>Only the current simulated day has data right after a fresh start.</p>
              </div>
            </section>
          ) : (
            <>
              <section className="time-full time-sum" aria-live="polite">
                <p className="time-sentence">
                  <strong>{name}</strong> spent about <strong className="num">{minutes(fresh.total_minutes)}</strong> online{' '}
                  {dayWords(dayIdx, day?.label ?? '')}, in <span className="num">{fresh.sessions}</span>{' '}
                  {fresh.sessions === 1 ? 'session' : 'sessions'}.{' '}
                  <span className="badge badge-plain">estimate</span>
                </p>
                <p className="time-note">{fresh.note || meta.data?.estimate_note}</p>
              </section>

              <section className="panel time-cats" aria-labelledby="t-cat">
                <div className="panel-head"><h2 id="t-cat">By category</h2></div>
                <div
                  className="panel-pad"
                  role="img"
                  aria-label={`Estimated time by category for ${name}: ${cats.map(([c, v]) => `${categoryLabel(c)} ${minutes(v)}`).join(', ')}.`}
                >
                  <ul className="cat-list" aria-hidden>
                    {cats.map(([c, v]) => (
                      <li key={c}>
                        <span className="cat-name">{categoryLabel(c)}</span>
                        <span className="cat-track">
                          <span className="cat-fill" style={{ width: `${Math.max(2, (v / maxCat) * 100)}%`, background: catColor(c) }} />
                        </span>
                        <span className="num cat-val">{minutes(v)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>

              <section className="panel time-hours" aria-labelledby="t-hour">
                <div className="panel-head"><h2 id="t-hour">Time of day</h2><span className="time-muted">minutes per hour, estimate</span></div>
                <div
                  className="panel-pad"
                  role="img"
                  aria-label={`Estimated minutes online in each hour of the day for ${name}. Busiest hour: ${pad(peak.h)}:00 to ${pad((peak.h + 1) % 24)}:00, about ${Math.round(peak.min)} minutes. Night, 22:00 to 06:00, is shaded.`}
                >
                  <div className="hours-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={hours} margin={{ top: 18, right: 4, bottom: 0, left: -12 }} barCategoryGap="18%">
                        <CartesianGrid vertical={false} stroke="var(--line)" />
                        <ReferenceArea key="night-morning" x1="00" x2="05" fill="var(--viz-night)" fillOpacity={1} stroke="none"
                          label={{ value: 'Night', position: 'insideTop', fill: 'var(--muted)', fontSize: 12 }} />
                        <ReferenceArea key="night-evening" x1="22" x2="23" ifOverflow="visible" fill="var(--viz-night)" fillOpacity={1} stroke="none"
                          label={{ value: 'Night', position: 'insideTop', fill: 'var(--muted)', fontSize: 12 }} />
                        <XAxis dataKey="label" interval={2} tickLine={false} axisLine={{ stroke: 'var(--line-strong)' }}
                          tick={{ fill: 'var(--muted)', fontSize: 12 }} />
                        <YAxis width={44} tickLine={false} axisLine={false} tickFormatter={(v: number) => `${v}`}
                          tick={{ fill: 'var(--muted)', fontSize: 12 }} />
                        <Tooltip content={<HourTip />} cursor={{ fill: 'var(--surface-2)' }} isAnimationActive={false} />
                        <Bar dataKey="min" fill="var(--viz-1)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </section>

              <section className="panel time-full" aria-labelledby="t-sites">
                <div className="panel-head"><h2 id="t-sites">Top sites</h2><span className="time-muted">estimate</span></div>
                {hasExplicit && !showSites ? (
                  <div className="panel-pad time-hidden">
                    <span>Some of this time was on explicit sites, so site names are hidden.</span>
                    <button className="btn btn-secondary" onClick={() => setShowSites(true)}>Show site names</button>
                  </div>
                ) : (
                  <ol className="site-list">
                    {sites.map(([s, v]) => (
                      <li key={s}>
                        <span className="mono domain">{s}</span>
                        <span className="site-track" aria-hidden>
                          <span className="site-fill" style={{ width: `${Math.max(2, (v / maxSite) * 100)}%` }} />
                        </span>
                        <span className="num site-val">{minutes(v)}</span>
                      </li>
                    ))}
                  </ol>
                )}
              </section>
            </>
          )}
        </div>
      )}
    </div>
  )
}
