import { useCallback, useRef, useState } from 'react'
import ReactCrop, { type Crop, centerCrop, makeAspectCrop } from 'react-image-crop'
import 'react-image-crop/dist/ReactCrop.css'
import api from '../api'

interface Props {
  subjects: { id: string; name: string }[]
  onComplete: (questionId: string) => void
}

function getCroppedBlob(image: HTMLImageElement, crop: Crop): Promise<Blob> {
  const canvas = document.createElement('canvas')
  const scaleX = image.naturalWidth / image.width
  const scaleY = image.naturalHeight / image.height
  canvas.width = crop.width * scaleX
  canvas.height = crop.height * scaleY
  const ctx = canvas.getContext('2d')!
  ctx.drawImage(image, crop.x * scaleX, crop.y * scaleY, crop.width * scaleX, crop.height * scaleY, 0, 0, canvas.width, canvas.height)
  return new Promise((resolve) => canvas.toBlob((b) => resolve(b!), 'image/jpeg', 0.9))
}

export default function CaptureFlow({ subjects, onComplete }: Props) {
  const [step, setStep] = useState<'select-subject' | 'crop' | 'ocr'>('select-subject')
  const [subjectId, setSubjectId] = useState('')
  const [imgSrc, setImgSrc] = useState('')
  const [crop, setCrop] = useState<Crop>()
  const [completedCrop, setCompletedCrop] = useState<Crop>()
  const imgRef = useRef<HTMLImageElement>(null)
  const [ocrText, setOcrText] = useState('')
  const [questionId, setQuestionId] = useState('')
  const [uploading, setUploading] = useState(false)
  const [ocrStatus, setOcrStatus] = useState<'pending' | 'done' | 'failed'>('pending')

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const reader = new FileReader()
      reader.onload = () => { setImgSrc(reader.result as string); setStep('crop') }
      reader.readAsDataURL(e.target.files[0])
    }
  }

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget
    setCrop(centerCrop(makeAspectCrop({ unit: '%', width: 90 }, 4 / 3, width, height), width, height))
  }

  const submitCrop = async () => {
    if (!imgRef.current || !completedCrop) return
    setUploading(true)
    const blob = await getCroppedBlob(imgRef.current, completedCrop)
    const form = new FormData()
    form.append('file', blob, 'question.jpg')
    if (subjectId) form.append('subject_id', subjectId)

    const { data } = await api.post('/questions/upload', form)
    setQuestionId(data.question_id)
    setStep('ocr')
    pollOcr(data.question_id)
    setUploading(false)
  }

  const pollOcr = async (qid: string) => {
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 1000))
      const { data } = await api.get(`/questions/${qid}/ocr-status`)
      if (data.ocr_status === 'done') {
        setOcrText(data.ocr_verified_text ?? '')
        setOcrStatus('done')
        return
      }
      if (data.ocr_status === 'failed') { setOcrStatus('failed'); return }
    }
    setOcrStatus('failed')
  }

  const saveOcr = async () => {
    await api.put(`/questions/${questionId}/ocr`, { ocr_verified_text: ocrText })
    onComplete(questionId)
  }

  if (step === 'select-subject') return (
    <div style={{ padding: 24 }}>
      <h3>选择科目</h3>
      {subjects.length === 0 && <p style={{ color: 'orange' }}>请先在后台创建科目</p>}
      <select value={subjectId} onChange={e => setSubjectId(e.target.value)} style={{ display: 'block', marginBottom: 16, width: '100%', fontSize: 16 }}>
        <option value="">-- 选择科目 --</option>
        {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      <label style={{ display: 'block', marginBottom: 8 }}>
        <span>拍照或选图</span>
        <input type="file" accept="image/*" capture="environment" onChange={onFileChange} style={{ display: 'block', marginTop: 8 }} />
      </label>
    </div>
  )

  if (step === 'crop') return (
    <div style={{ padding: 24 }}>
      <h3>裁剪题目区域</h3>
      <ReactCrop crop={crop} onChange={c => setCrop(c)} onComplete={c => setCompletedCrop(c)}>
        <img ref={imgRef} src={imgSrc} onLoad={onImageLoad} style={{ maxWidth: '100%' }} />
      </ReactCrop>
      <button onClick={submitCrop} disabled={uploading} style={{ marginTop: 16, width: '100%', padding: '12px 0', fontSize: 16 }}>
        {uploading ? '上传中...' : '确认上传'}
      </button>
    </div>
  )

  return (
    <div style={{ padding: 24 }}>
      <h3>核对 OCR 识别结果</h3>
      {ocrStatus === 'pending' && <p>正在识别中，请稍候...</p>}
      {ocrStatus === 'failed' && <p style={{ color: 'red' }}>识别失败，请手动输入题目内容</p>}
      {(ocrStatus === 'done' || ocrStatus === 'failed') && (
        <>
          <textarea
            value={ocrText}
            onChange={e => setOcrText(e.target.value)}
            rows={8}
            style={{ width: '100%', fontSize: 15, marginBottom: 16 }}
            placeholder="题目内容..."
          />
          <button onClick={saveOcr} style={{ width: '100%', padding: '12px 0', fontSize: 16 }}>保存题目</button>
        </>
      )}
    </div>
  )
}
