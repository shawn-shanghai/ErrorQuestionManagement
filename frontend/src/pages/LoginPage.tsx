import { useState } from 'react'
import api from '../api'

interface Props {
  onSuccess: (token: string) => void
}

export default function LoginPage({ onSuccess }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      if (mode === 'login') {
        const { data } = await api.post('/auth/login', { email, password })
        onSuccess(data.access_token)
      } else {
        const { data } = await api.post('/auth/register', { username, email, password })
        onSuccess(data.access_token)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? '请求失败')
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: '80px auto', padding: 24 }}>
      <h2>{mode === 'login' ? '登录' : '注册'}</h2>
      <form onSubmit={submit}>
        {mode === 'register' && (
          <div>
            <label>用户名</label>
            <input value={username} onChange={e => setUsername(e.target.value)} required style={{ display: 'block', width: '100%', marginBottom: 12 }} />
          </div>
        )}
        <div>
          <label>邮箱</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ display: 'block', width: '100%', marginBottom: 12 }} />
        </div>
        <div>
          <label>密码</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} style={{ display: 'block', width: '100%', marginBottom: 12 }} />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" style={{ width: '100%', padding: '10px 0' }}>
          {mode === 'login' ? '登录' : '注册'}
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: 16 }}>
        {mode === 'login' ? (
          <span>没有账户？<button onClick={() => setMode('register')}>注册</button></span>
        ) : (
          <span>已有账户？<button onClick={() => setMode('login')}>登录</button></span>
        )}
      </p>
    </div>
  )
}
