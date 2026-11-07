import { Eye } from 'lucide-react'
import { useState } from 'react'

/** A site name as network data. Explicit sites stay hidden until a parent clicks Show (D23). */
export function Domain({ domain, category }: { domain: string; category: string }) {
  const [shown, setShown] = useState(false)
  if (category !== 'explicit' || shown) return <span className="mono domain">{domain}</span>
  return (
    <span className="domain-hidden">
      <span>Explicit site (hidden)</span>
      <button className="btn btn-ghost domain-show" onClick={() => setShown(true)} aria-label="Show the site name">
        <Eye /> Show
      </button>
    </span>
  )
}
