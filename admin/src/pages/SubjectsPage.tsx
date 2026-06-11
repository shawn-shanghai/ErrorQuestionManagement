import { useEffect, useState } from 'react'
import api from '../api'

interface Subject { id: string; name: string; description: string | null }

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const load = async () => {
    const { data } = await api.get('/subjects')
    setSubjects(data)
  }

  useEffect(() => { load() }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      if (editId) {
        await api.put(`/subjects/${editId}`, { name, description })
      } else {
        await api.post('/subjects', { name, description })
      }
      setName(''); setDescription(''); setEditId(null)
      load()
    } catch (err: any) {
      setError(err.response?.data?.detail ?? '操作失败')
    }
  }

  const startEdit = (s: Subject) => { setEditId(s.id); setName(s.name); setDescription(s.description ?? '') }

  const remove = async (id: string, subjectName: string) => {
    if (!confirm(`确定删除科目"${subjectName}"？该科目下的题目将变为无科目状态。`)) return
    await api.delete(`/subjects/${id}`)
    load()
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>科目管理</h2>
      <form onSubmit={save} style={{ marginBottom: 24 }}>
        <input placeholder="科目名称" value={name} onChange={e => setName(e.target.value)} required style={{ marginRight: 8 }} />
        <input placeholder="描述（可选）" value={description} onChange={e => setDescription(e.target.value)} style={{ marginRight: 8 }} />
        <button type="submit">{editId ? '保存修改' : '添加科目'}</button>
        {editId && <button type="button" onClick={() => { setEditId(null); setName(''); setDescription('') }} style={{ marginLeft: 8 }}>取消</button>}
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr><th>名称</th><th>描述</th><th>操作</th></tr></thead>
        <tbody>
          {subjects.map(s => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.description}</td>
              <td>
                <button onClick={() => startEdit(s)} style={{ marginRight: 8 }}>编辑</button>
                <button onClick={() => remove(s.id, s.name)}>删除</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
