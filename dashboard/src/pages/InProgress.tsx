import { Hammer } from 'lucide-react'

// Honest placeholder for screens not built yet (nothing is claimed that is not true).
export function InProgress({ title, step, what }: { title: string; step: string; what: string }) {
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>{what}</p>
        </div>
      </div>
      <div className="panel empty">
        <Hammer aria-hidden="true" style={{ width: 28, height: 28, color: 'var(--muted)', marginBottom: 12 }} />
        <h2>This screen is being built</h2>
        <p>It arrives in plan step {step}.</p>
      </div>
    </div>
  )
}
