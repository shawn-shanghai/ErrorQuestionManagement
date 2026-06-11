import { useEffect, useState } from 'react'
import api from './api'
import LoginPage from './pages/LoginPage'
import ReviewPage from './pages/ReviewPage'
import StudyStatsPage from './pages/StudyStatsPage'
import CaptureFlow from './components/CaptureFlow'
import './App.css'

type Tab = 'capture' | 'review' | 'stats'
interface Subject { id: string; name: string }

export default function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [tab, setTab] = useState<Tab>('capture')
  const [subjects, setSubjects] = useState<Subject[]>([])

  useEffect(() => {
    if (!token) return
    api.get('/subjects').then(r => setSubjects(r.data)).catch(() => {})
  }, [token])

  const handleLogin = (accessToken: string) => {
    localStorage.setItem('access_token', accessToken)
    setToken(accessToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    setToken(null)
  }

  if (!token) return <LoginPage onSuccess={handleLogin} />

  return (
    <div className="app">
      <main className="app-main">
        {tab === 'capture' && (
          <CaptureFlow subjects={subjects} onComplete={() => setTab('review')} />
        )}
        {tab === 'review' && <ReviewPage />}
        {tab === 'stats' && <StudyStatsPage />}
      </main>

      <nav className="tab-bar">
        <button className={tab === 'capture' ? 'active' : ''} onClick={() => setTab('capture')}>拍照</button>
        <button className={tab === 'review' ? 'active' : ''} onClick={() => setTab('review')}>复习</button>
        <button className={tab === 'stats' ? 'active' : ''} onClick={() => setTab('stats')}>统计</button>
        <button onClick={handleLogout}>退出</button>
      </nav>
    </div>
  )
}
