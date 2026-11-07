import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, get } from './api'

/** GET `path` now and every `ms` (default 5 s, the server's simulation tick). `reload()` refreshes at once. */
export function usePoll<T>(path: string | null, ms = 5000) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const alive = useRef(true)

  const reload = useCallback(async () => {
    if (!path) return
    try {
      const d = await get<T>(path)
      if (alive.current) {
        setData(d)
        setError(null)
      }
    } catch (e) {
      if (alive.current) setError(e instanceof ApiError ? e.message : 'The server could not be reached.')
    } finally {
      if (alive.current) setLoading(false)
    }
  }, [path])

  useEffect(() => {
    alive.current = true
    setLoading(true)
    reload()
    if (!ms) return () => { alive.current = false }
    const t = window.setInterval(reload, ms)
    return () => {
      alive.current = false
      window.clearInterval(t)
    }
  }, [reload, ms])

  return { data, error, loading, reload }
}
