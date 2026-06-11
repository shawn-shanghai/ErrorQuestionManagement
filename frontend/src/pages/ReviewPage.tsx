import { useEffect, useState } from 'react'
import api from '../api'
import FlashcardReview from '../components/FlashcardReview'

interface Subject { id: string; name: string }
interface Tag { id: string; name: string }

export default function ReviewPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [selectedSubject, setSelectedSubject] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [mode, setMode] = useState<'filter' | 'review'>('filter')

  useEffect(() => {
    Promise.all([api.get('/subjects'), api.get('/tags')]).then(([sRes, tRes]) => {
      setSubjects(sRes.data)
      setTags(tRes.data)
    })
  }, [])

  const toggleTag = (id: string) =>
    setSelectedTags(prev => prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id])

  if (mode === 'review') return (
    <div>
      <button onClick={() => setMode('filter')} style={{ margin: 16 }}>← 返回筛选</button>
      <FlashcardReview subjectId={selectedSubject || undefined} tagIds={selectedTags} />
    </div>
  )

  return (
    <div style={{ padding: 24 }}>
      <h2>开始复习</h2>

      {/* Subject selector */}
      <div style={{ marginBottom: 20 }}>
        <h4 style={{ marginBottom: 8 }}>选择科目</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <button
            onClick={() => setSelectedSubject('')}
            style={{ padding: '8px 16px', borderRadius: 20, background: !selectedSubject ? '#4f46e5' : '#f0f0f0', color: !selectedSubject ? '#fff' : '#333', border: 'none' }}
          >全部</button>
          {subjects.map(s => (
            <button key={s.id} onClick={() => setSelectedSubject(s.id)}
              style={{ padding: '8px 16px', borderRadius: 20, background: selectedSubject === s.id ? '#4f46e5' : '#f0f0f0', color: selectedSubject === s.id ? '#fff' : '#333', border: 'none' }}>
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Multi-tag selector (AND logic) */}
      <div style={{ marginBottom: 20 }}>
        <h4 style={{ marginBottom: 8 }}>筛选标签（同时满足）</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {tags.map(t => (
            <button key={t.id} onClick={() => toggleTag(t.id)}
              style={{ padding: '6px 14px', borderRadius: 20, background: selectedTags.includes(t.id) ? '#0ea5e9' : '#f0f0f0', color: selectedTags.includes(t.id) ? '#fff' : '#333', border: 'none', fontSize: 13 }}>
              {t.name}
            </button>
          ))}
          {tags.length === 0 && <span style={{ color: '#999' }}>暂无标签，请在后台创建</span>}
        </div>
      </div>

      <button
        onClick={() => setMode('review')}
        style={{ width: '100%', padding: '14px 0', fontSize: 16, background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 10 }}
      >
        开始复习
      </button>
    </div>
  )
}
