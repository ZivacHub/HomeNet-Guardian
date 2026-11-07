// The mark: a roof line over three Wi-Fi arcs. Drawn here so it stays crisp in both themes.
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="logo">
      <rect width="32" height="32" rx="8" fill="var(--accent)" />
      <path d="M7 15.5 16 8l9 7.5" fill="none" stroke="var(--accent-ink)" strokeWidth="2.2"
        strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10.6 19.2a7.6 7.6 0 0 1 10.8 0" fill="none" stroke="var(--accent-ink)" strokeWidth="2.2"
        strokeLinecap="round" />
      <path d="M13.2 21.9a3.9 3.9 0 0 1 5.6 0" fill="none" stroke="var(--accent-ink)" strokeWidth="2.2"
        strokeLinecap="round" />
      <circle cx="16" cy="24.6" r="1.5" fill="var(--accent-ink)" />
    </svg>
  )
}
