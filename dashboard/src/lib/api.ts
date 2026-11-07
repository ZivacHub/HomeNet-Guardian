// Small fetch wrapper for the local HomeNet Guardian server (/api is proxied to 127.0.0.1:8000).

export type Parent = { id: number; username: string; display_name: string }

export class ApiError extends Error {
  status: number
  code: string | null
  constructor(status: number, message: string, code: string | null = null) {
    super(message)
    this.status = status
    this.code = code
  }
}

type Listener = (e: ApiError) => void
const listeners = new Set<Listener>()

/** The app shell listens here: 401 sends you to login, 403 consent_required to the consent step. */
export function onAuthProblem(fn: Listener): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export async function api<T = unknown>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, headers, ...rest } = init
  const res = await fetch(`/api${path}`, {
    credentials: 'same-origin',
    ...rest,
    headers: { ...(json !== undefined ? { 'Content-Type': 'application/json' } : {}), ...headers },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  })
  if (res.ok) return (res.status === 204 ? undefined : await res.json()) as T

  let message = `The server answered ${res.status}.`
  let code: string | null = null
  try {
    const body = await res.json()
    const d = body?.detail
    if (typeof d === 'string') message = d
    else if (d && typeof d === 'object' && 'message' in d) {
      message = String(d.message)
      code = 'code' in d ? String(d.code) : null
    } else if (Array.isArray(d) && d[0]?.msg) message = String(d[0].msg)
  } catch {
    /* no JSON body */
  }
  const err = new ApiError(res.status, message, code)
  const isAuthRoute = path.startsWith('/auth/login')
  if (!isAuthRoute && (res.status === 401 || code === 'consent_required')) listeners.forEach((fn) => fn(err))
  throw err
}

export const get = <T,>(path: string) => api<T>(path)
export const post = <T,>(path: string, json?: unknown) => api<T>(path, { method: 'POST', json: json ?? {} })
export const patch = <T,>(path: string, json: unknown) => api<T>(path, { method: 'PATCH', json })
export const put = <T,>(path: string, json: unknown) => api<T>(path, { method: 'PUT', json })
export const del = <T,>(path: string) => api<T>(path, { method: 'DELETE' })
