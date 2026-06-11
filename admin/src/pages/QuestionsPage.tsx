import { useEffect, useState } from 'react'
import api from '../api'

interface Question {
  id: string; ocr_raw_text: string; ocr_verified_text: string
  subject_id: string; status: string; image_url: string; created_at: string
}
interface Subject { id: string; name: string }
interface Tag { id: string; name: string }

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [filterSubject, setFilterSubject] = useState('')
  const [editQ, setEditQ] = useState<Question | null>(null)
  const [editForm, setEditForm] = useState({ ocr_verified_text: '', answer_text: '', status: '', subject_id: '', tag_ids: [] as string[] })
  const [batchForm, setBatchForm] = useState({ subject_id: '', add_tag_ids: [] as string[], status: '' })

  const load = async () => {
    const params = filterSubject ? `?subject_id=${filterSubject}` : ''
    const [qRes, sRes, tRes] = await Promise.all([
      api.get(`/admin/questions/pending${params}`),
      api.get('/subjects'),
      api.get('/tags'),
    ])
    setQuestions(qRes.data)
    setSubjects(sRes.data)
    setTags(tRes.data)
  }

  useEffect(() => { load() }, [filterSubject])

  const openEdit = async (q: Question) => {
    const { data } = await api.get(`/questions/${q.id}`)
    setEditQ(q)
    setEditForm({
      ocr_verified_text: data.ocr_verified_text ?? '',
      answer_text: data.answer_text ?? '',
      status: data.status,
      subject_id: data.subject_id ?? '',
      tag_ids: data.tags.map((t: any) => t.id),
    })
  }

  const saveEdit = async () => {
    if (!editQ) return
    await api.put(`/admin/questions/${editQ.id}`, editForm)
    setEditQ(null)
    load()
  }

  const batchSubmit = async () => {
    if (selected.size === 0) return alert('请先选择题目')
    await api.post('/admin/questions/batch', { question_ids: [...selected], ...batchForm })
    setSelected(new Set())
    load()
  }

  const toggle = (id: string) => setSelected(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s })

  return (
    <div style={{ padding: 24 }}>
      <h2>题目管理（待验证 OCR）</h2>

      {/* Filter */}
      <select value={filterSubject} onChange={e => setFilterSubject(e.target.value)} style={{ marginBottom: 16 }}>
        <option value="">全部科目</option>
        {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>

      {/* Batch actions */}
      {selected.size > 0 && (
        <div style={{ background: '#f0f0f0', padding: 12, marginBottom: 16, borderRadius: 6 }}>
          <strong>已选 {selected.size} 道题</strong>
          <select value={batchForm.subject_id} onChange={e => setBatchForm(f => ({ ...f, subject_id: e.target.value }))} style={{ marginLeft: 12 }}>
            <option value="">批量修改科目...</option>
            {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <select value={batchForm.status} onChange={e => setBatchForm(f => ({ ...f, status: e.target.value }))} style={{ marginLeft: 8 }}>
            <option value="">批量修改状态...</option>
            <option value="active">active</option>
            <option value="archived">archived</option>
          </select>
          <button onClick={batchSubmit} style={{ marginLeft: 12 }}>批量应用</button>
        </div>
      )}

      {/* Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr>
            <th><input type="checkbox" onChange={e => setSelected(e.target.checked ? new Set(questions.map(q => q.id)) : new Set())} /></th>
            <th>图片</th><th>OCR 原文</th><th>校正文本</th><th>科目</th><th>状态</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          {questions.map(q => (
            <tr key={q.id} style={{ borderBottom: '1px solid #eee' }}>
              <td><input type="checkbox" checked={selected.has(q.id)} onChange={() => toggle(q.id)} /></td>
              <td><img src={q.image_url} alt="" style={{ width: 80, height: 60, objectFit: 'cover' }} /></td>
              <td style={{ maxWidth: 200, overflow: 'hidden' }}>{q.ocr_raw_text}</td>
              <td style={{ maxWidth: 200, overflow: 'hidden' }}>{q.ocr_verified_text}</td>
              <td>{subjects.find(s => s.id === q.subject_id)?.name ?? '-'}</td>
              <td>{q.status}</td>
              <td><button onClick={() => openEdit(q)}>编辑</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Edit modal */}
      {editQ && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: '#fff', padding: 24, borderRadius: 8, width: 500, maxHeight: '80vh', overflowY: 'auto' }}>
            <h3>编辑题目</h3>
            <img src={editQ.image_url} alt="" style={{ width: '100%', marginBottom: 12 }} />
            <label>校正文本</label>
            <textarea value={editForm.ocr_verified_text} onChange={e => setEditForm(f => ({ ...f, ocr_verified_text: e.target.value }))} rows={5} style={{ width: '100%', marginBottom: 8 }} />
            <label>答案</label>
            <textarea value={editForm.answer_text} onChange={e => setEditForm(f => ({ ...f, answer_text: e.target.value }))} rows={4} style={{ width: '100%', marginBottom: 8 }} />
            <label>科目</label>
            <select value={editForm.subject_id} onChange={e => setEditForm(f => ({ ...f, subject_id: e.target.value }))} style={{ display: 'block', width: '100%', marginBottom: 8 }}>
              <option value="">无科目</option>
              {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <label>标签</label>
            <div style={{ marginBottom: 8 }}>
              {tags.map(t => (
                <label key={t.id} style={{ marginRight: 12 }}>
                  <input type="checkbox" checked={editForm.tag_ids.includes(t.id)}
                    onChange={e => setEditForm(f => ({ ...f, tag_ids: e.target.checked ? [...f.tag_ids, t.id] : f.tag_ids.filter(id => id !== t.id) }))} />
                  {t.name}
                </label>
              ))}
            </div>
            <label>状态</label>
            <select value={editForm.status} onChange={e => setEditForm(f => ({ ...f, status: e.target.value }))} style={{ display: 'block', width: '100%', marginBottom: 16 }}>
              <option value="pending">pending</option>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
            <button onClick={saveEdit} style={{ marginRight: 12 }}>保存</button>
            <button onClick={() => setEditQ(null)}>取消</button>
          </div>
        </div>
      )}
    </div>
  )
}
