// Light by default (D7); the switch is remembered in this browser (D24).
export type Theme = 'light' | 'dark'
const KEY = 'hg-theme'

export function loadTheme(): Theme {
  try {
    const saved = localStorage.getItem(KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    /* storage blocked: fall back to light */
  }
  return 'light'
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    /* ignore */
  }
}
