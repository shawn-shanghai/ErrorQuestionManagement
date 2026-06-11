import { useEffect, useState } from 'react'
import api from '../api'

interface Tag { id: string; name: string }

export default function TagsPage() {
  const [tags, setTags] = useState<Tag[]>([])
  const [name, setName] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const load = async () => {
    const { data } = await api.get('/tags')
    setTags(data)
  }

  useEffect(() => { load() }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      if (editId) {
        await api.put(`/tags/${editId}`, { name })
      } else {
        await api.post('/tags', { name })
      }
      setName(''); setEditId(null)
      load()
    } catch (err: any) {
      setError(err.response?.data?.detail ?? '操作失败')
    }
  }

  const remove = async (id: string, tagName: string) => {
    if (!confirm(`确定删除标签"${tagName}"？该标签与题目的关联将全部解除。`)) return
    await api.delete(`/tags/${id}`)
    load()
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>标签管理</h2>
      <form onSubmit={save} style={{ marginBottom: 24 }}>
        <input placeholder="标签名称" value={name} onChange={e => setName(e.target.value)} required style={{ marginRight: 8 }} />
        <button type="submit">{editId ? '保存修改' : '添加标签'}</button>
        {editId && <button type="button" onClick={() => { setEditId(null); setName('') }} style={{ marginLeft: 8 }}>取消</button>}
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <ul>
        {tags.map(t => (
          <li key={t.id} style={{ marginBottom: 8 }}>
            {t.name}
            <button onClick={() => { setEditId(t.id); setName(t.name) }} style={{ marginLeft: 12 }}>编辑</button>
            <button onClick={() => remove(t.id, t.name)} style={{ marginLeft: 8 }}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
