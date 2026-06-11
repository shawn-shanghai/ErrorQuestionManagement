import { useEffect, useRef, useState } from 'react'
import api from '../api'

interface Props {
  subjectId?: string
  tagIds?: string[]
}

interface Card {
  id: string
  image_url: string
  ocr_verified_text: string | null
  answer_text: string | null
}

export default function FlashcardReview({ subjectId, tagIds = [] }: Props) {
  const [card, setCard] = useState<Card | null>(null)
  const [flipped, setFlipped] = useState(false)
  const [done, setDone] = useState(false)
  const [reviewed, setReviewed] = useState<string[]>([])
  const startTime = useRef<number>(Date.now())

  const loadNext = async (excludeIds: string[]) => {
    setFlipped(false)
    startTime.current = Date.now()
    const params = new URLSearchParams()
    if (subjectId) params.append('subject_id', subjectId)
    tagIds.forEach(t => params.append('tag_ids', t))
    excludeIds.forEach(id => params.append('exclude_ids', id))
    const { data } = await api.get(`/review/next?${params}`)
    if (!data) { setDone(true); setCard(null) }
    else setCard(data)
  }

  useEffect(() => {
    setReviewed([])
    setDone(false)
    loadNext([])
  }, [subjectId, JSON.stringify(tagIds)])

  const submit = async (isCorrect: boolean) => {
    if (!card) return
    const duration = Math.round((Date.now() - startTime.current) / 1000)
    await api.post('/review/submit', { question_id: card.id, is_correct: isCorrect, duration_seconds: duration })
    const newReviewed = [...reviewed, card.id]
    setReviewed(newReviewed)
    loadNext(newReviewed)
  }

  if (done) return (
    <div style={{ padding: 32, textAlign: 'center' }}>
      <h3>本轮复习完成！</h3>
      <p>共复习了 {reviewed.length} 道题</p>
      <button onClick={() => { setReviewed([]); setDone(false); loadNext([]) }} style={{ padding: '12px 32px', fontSize: 16 }}>
        再来一轮
      </button>
    </div>
  )

  if (!card) return <div style={{ padding: 32, textAlign: 'center' }}>加载中...</div>

  return (
    <div style={{ padding: 24, maxWidth: 480, margin: '0 auto' }}>
      {/* Card */}
      <div style={{ border: '1px solid #ddd', borderRadius: 12, padding: 20, minHeight: 300, marginBottom: 20 }}>
        <img src={card.image_url} alt="题目" style={{ width: '100%', borderRadius: 8, marginBottom: 12 }} />
        {card.ocr_verified_text && (
          <p style={{ fontSize: 15, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{card.ocr_verified_text}</p>
        )}

        {!flipped ? (
          <button
            onClick={() => setFlipped(true)}
            style={{ width: '100%', padding: '14px 0', fontSize: 16, marginTop: 16, background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 8 }}
          >
            查看答案
          </button>
        ) : (
          <>
            <hr style={{ margin: '16px 0' }} />
            {card.answer_text ? (
              <p style={{ fontSize: 15, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{card.answer_text}</p>
            ) : (
              <p style={{ color: '#999' }}>该题暂无答案，请在后台录入</p>
            )}
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                onClick={() => submit(true)}
                style={{ flex: 1, padding: '14px 0', fontSize: 16, background: '#22c55e', color: '#fff', border: 'none', borderRadius: 8 }}
              >
                答对了 ✓
              </button>
              <button
                onClick={() => submit(false)}
                style={{ flex: 1, padding: '14px 0', fontSize: 16, background: '#ef4444', color: '#fff', border: 'none', borderRadius: 8 }}
              >
                答错了 ✗
              </button>
            </div>
          </>
        )}
      </div>

      <p style={{ textAlign: 'center', color: '#999', fontSize: 13 }}>本轮已复习 {reviewed.length} 题</p>
    </div>
  )
}
