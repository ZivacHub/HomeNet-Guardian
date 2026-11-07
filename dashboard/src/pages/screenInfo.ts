import type { RouteId } from '../lib/routes'

// Page titles and one-line descriptions, shared by the placeholders and the real screens.
export const SCREEN_INFO: Record<RouteId, { title: string; step: string; what: string }> = {
  overview: { title: 'Overview', step: '3.2', what: 'Who is online, today per child, and warnings that need you.' },
  devices: { title: 'Devices', step: '3.3', what: 'Every device on the home Wi-Fi, and whose it is.' },
  activity: { title: 'Live activity', step: '3.4', what: 'Each site a device asks for, as it happens.' },
  time: { title: 'Where time goes', step: '3.5', what: 'An estimate of time per category and site, for each child.' },
  rules: { title: 'Rules', step: '3.6', what: 'Blocked categories, bedtimes and the pause button.' },
  payments: { title: 'Payments & stores', step: '3.7', what: 'Store and payment sites wait for your OK.' },
  reports: { title: 'Reports', step: '4.2', what: 'Weekly and monthly summaries.' },
  settings: { title: 'Settings', step: '3.8', what: 'Records, parents, the family notice, and what this does not see.' },
}
