'use client'

import { useState, useRef, useEffect } from 'react'
import { Upload, File, AlertCircle, Loader } from 'lucide-react'
import toast from 'react-hot-toast'
import { useGetStatsQuery, useGetSourcesQuery, useGetJobStatusQuery } from '@/store/api/devflowApi'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const VALID_EXTS = ['.pdf', '.docx', '.txt']

export default function FileUpload() {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { refetch: refetchStats } = useGetStatsQuery()
  const { refetch: refetchSources } = useGetSourcesQuery()

  const { data: jobData } = useGetJobStatusQuery(jobId!, {
    skip: !jobId,
    pollingInterval: jobId ? 2000 : 0,
  })

  useEffect(() => {
    if (!jobData) return
    if (jobData.status === 'completed') {
      setJobId(null)
      toast.success(`Indexed ${jobData.filename} — ${jobData.chunks} chunks`)
      refetchStats()
      refetchSources()
    } else if (jobData.status === 'failed') {
      setJobId(null)
      setError(jobData.error || 'Indexing failed')
    }
  }, [jobData?.status])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!VALID_EXTS.includes(ext)) {
      setError('Upload a PDF, DOCX, or TXT file')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large — max 10 MB')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: formData })
      if (!res.ok) {
        const body = await res.json()
        throw new Error(body.detail || 'Upload failed')
      }
      const data = await res.json()
      setJobId(data.job_id)
      if (inputRef.current) inputRef.current.value = ''
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const isIndexing = !!jobId

  return (
    <div className="file-upload-section">
      <h3><Upload size={20} /> Upload Document</h3>
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="file-upload" className="btn btn-primary"
          style={{ cursor: uploading || isIndexing ? 'not-allowed' : 'pointer', opacity: uploading || isIndexing ? 0.6 : 1 }}>
          {isIndexing ? <Loader size={18} className="spin" /> : <File size={18} />}
          {uploading ? 'Uploading...' : isIndexing ? 'Indexing...' : 'Choose File (PDF, DOCX, TXT)'}
        </label>
        <input id="file-upload" ref={inputRef} type="file" accept=".pdf,.docx,.txt"
          onChange={handleFileChange} disabled={uploading || isIndexing} style={{ display: 'none' }} />
      </div>
      {isIndexing && (
        <div style={{ background: 'rgba(139,124,248,0.1)', color: '#a78bfa', padding: '10px 14px', borderRadius: 8, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8, border: '1px solid rgba(139,124,248,0.2)', fontSize: '0.9rem' }}>
          <Loader size={16} className="spin" style={{ flexShrink: 0 }} />
          Indexing in background — you can keep using the app
        </div>
      )}
      {error && <div className="error"><AlertCircle size={18} /> {error}</div>}
      <p style={{ fontSize: '0.85rem', color: '#475569', marginTop: 8 }}>PDF, DOCX, TXT — max 10 MB</p>
    </div>
  )
}
