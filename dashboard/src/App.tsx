import { useEffect, useState } from 'react'

type Status = 'checking' | 'connected' | 'unreachable'

function App() {
  const [status, setStatus] = useState<Status>('checking')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => (res.ok ? setStatus('connected') : setStatus('unreachable')))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <main>
      <h1>HomeNet Guardian</h1>
      <p>Home network dashboard for parents (simulated network)</p>
      <small>
        {status === 'checking'
          ? 'Backend: checking...'
          : status === 'connected'
            ? 'Backend: connected'
            : 'Backend: not reachable'}
      </small>
    </main>
  )
}

export default App
