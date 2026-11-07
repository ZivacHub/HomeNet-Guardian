// Shared wording and number formats, so every screen says things the same way.

export const CATEGORY_LABEL: Record<string, string> = {
  social: 'Social media',
  video: 'Video',
  games: 'Games',
  learning: 'School & learning',
  messaging: 'Messaging',
  music: 'Music',
  payments: 'Stores & payments',
  shopping: 'Shopping',
  news: 'News',
  search: 'Search',
  system: 'Background system',
  encrypted_dns: 'Encrypted DNS',
  explicit: 'Explicit',
  other: 'Other',
}

export const categoryLabel = (c: string) => CATEGORY_LABEL[c] ?? c

/** "2026-11-07T17:49:23" -> "17:49" (or with seconds). Times are already the home's local time. */
export function clock(ts: string | null | undefined, seconds = false): string {
  if (!ts) return '-'
  return ts.slice(11, seconds ? 19 : 16)
}

/** 168.6 -> "2 h 49 min", 12 -> "12 min". Always an estimate; callers add the word. */
export function minutes(m: number): string {
  const total = Math.round(m)
  if (total < 60) return `${total} min`
  const h = Math.floor(total / 60)
  const r = total % 60
  return r ? `${h} h ${r} min` : `${h} h`
}

/** Relative "x min ago" against the simulated now (ISO). */
export function ago(ts: string, nowIso: string): string {
  const diff = (Date.parse(nowIso) - Date.parse(ts)) / 60000
  if (diff < 1) return 'just now'
  if (diff < 60) return `${Math.round(diff)} min ago`
  return `at ${clock(ts)}`
}

export const KIND_LABEL: Record<string, string> = {
  phone: 'Phone', tablet: 'Tablet', laptop: 'Laptop', tv: 'TV', console: 'Game console', unknown: 'Unknown',
}
