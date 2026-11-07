import { useEffect, useState } from 'react'

// Hash routes keep the app a single static page (no router dependency).
export const ROUTES = [
  { id: 'overview', label: 'Overview' },
  { id: 'devices', label: 'Devices' },
  { id: 'activity', label: 'Live activity' },
  { id: 'time', label: 'Time' },
  { id: 'rules', label: 'Rules' },
  { id: 'payments', label: 'Payments' },
  { id: 'reports', label: 'Reports' },
  { id: 'settings', label: 'Settings' },
] as const

export type RouteId = (typeof ROUTES)[number]['id']

function current(): RouteId {
  const h = window.location.hash.replace(/^#\/?/, '').split('?')[0]
  return (ROUTES.find((r) => r.id === h)?.id ?? 'overview') as RouteId
}

export function useRoute(): RouteId {
  const [route, setRoute] = useState<RouteId>(current)
  useEffect(() => {
    const on = () => setRoute(current())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

export const href = (id: RouteId) => `#/${id}`
