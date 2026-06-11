import { useEffect, useState } from 'react'
import api from '../api'

interface Tag { id: string; name: string }
interface Stats {
  total_reviews: number
  correct_reviews: number
  accuracy_rate: number | null
  last_reviewed_at: string | null
}
interface HistoryItem {
  event_id: string
  question_id: string
  image_url: string
  ocr_verified_text: string | null
  is_correct: boolean
  reviewed_at: string
}

export default function StudyStatsPage() {
  const [tags, setTags] = useState<Tag[]>([])
  const [selectedTag, setSelectedTag] = useState('')
  const [stats, setStats] = useState<Stats | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [page, setPage] = useState(1)

  useEffect(() => {
    api.get('/tags').then(r => setTags(r.data))
  }, [])

  useEffect(() => {
    const params = selectedTag ? `?tag_id=${selectedTag}` : ''
    api.get(`/study/stats${params}`).then(r => setStats(r.data))
    api.get(`/study/history?page=${page}`).then(r => setHistory(r.data))
  }, [selectedTag, page])

  return (
    <div style={{ padding: 24 }}>
      <h2>学习统计</h2>

      {/* Tag filter */}
      <select value={selectedTag} onChange={e => setSelectedTag(e.target.value)} style={{ marginBottom: 20, width: '100%', fontSize: 15, padding: 8 }}>
        <option value="">全部标签</option>
        {tags.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
      </select>

      {/* Stats card */}
      {stats && (
        <div style={{ background: '#f8fafc', borderRadius: 12, padding: 20, marginBottom: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div><div style={{ fontSize: 12, color: '#666' }}>总复习次数</div><div style={{ fontSize: 28, fontWeight: 700 }}>{stats.total_reviews}</div></div>
            <div><div style={{ fontSize: 12, color: '#666' }}>正确次数</div><div style={{ fontSize: 28, fontWeight: 700, color: '#22c55e' }}>{stats.correct_reviews}</div></div>
            <div><div style={{ fontSize: 12, color: '#666' }}>正确率</div><div style={{ fontSize: 28, fontWeight: 700, color: '#4f46e5' }}>{stats.accuracy_rate !== null ? `${(stats.accuracy_rate * 100).toFixed(0)}%` : 'N/A'}</div></div>
            <div><div style={{ fontSize: 12, color: '#666' }}>最近复习</div><div style={{ fontSize: 13, marginTop: 4 }}>{stats.last_reviewed_at ? new Date(stats.last_reviewed_at).toLocaleDateString('zh-CN') : '从未'}</div></div>
          </div>
        </div>
      )}

      {/* History list */}
      <h3>复习历史</h3>
      {history.map(item => (
        <div key={item.event_id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
          <img src={item.image_url} alt="" style={{ width: 56, height: 42, objectFit: 'cover', borderRadius: 6 }} />
          <div style={{ flex: 1, fontSize: 13, color: '#444', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.ocr_verified_text ?? '（无文字）'}
          </div>
          <div style={{ fontSize: 20 }}>{item.is_correct ? '✓' : '✗'}</div>
          <div style={{ fontSize: 11, color: '#999', whiteSpace: 'nowrap' }}>
            {new Date(item.reviewed_at).toLocaleDateString('zh-CN')}
          </div>
        </div>
      ))}

      {history.length > 0 && (
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          {page > 1 && <button onClick={() => setPage(p => p - 1)} style={{ marginRight: 12 }}>上一页</button>}
          <span style={{ fontSize: 13, color: '#999' }}>第 {page} 页</span>
          {history.length === 20 && <button onClick={() => setPage(p => p + 1)} style={{ marginLeft: 12 }}>下一页</button>}
        </div>
      )}
    </div>
  )
}
