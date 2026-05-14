'use client'

import { useState, useRef } from 'react'
import { Upload, File, CheckCircle, AlertCircle } from 'lucide-react'
import { useGetStatsQuery, useGetSourcesQuery } from '@/store/api/devflowApi'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const VALID_EXTS = ['.pdf', '.docx', '.txt']

export default function FileUpload() {
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { refetch: refetchStats } = useGetStatsQuery()
  const { refetch: refetchSources } = useGetSourcesQuery()

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (!VALID_EXTS.includes(ext)) {
      setError('Please upload a PDF, DOCX, or TXT file')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum 10MB')
      return
    }

    setUploading(true)
    setError(null)
    setMessage(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API_URL}/api/upload`, { method: 'POST', body: formData })
      if (!res.ok) {
        const body = await res.json()
        throw new Error(body.detail || 'Upload failed')
      }
      const data = await res.json()
      setMessage(`Uploaded ${file.name} — ${data.chunks} chunks indexed`)
      if (inputRef.current) inputRef.current.value = ''
      refetchStats()
      refetchSources()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="file-upload-section">
      <h3><Upload size={20} /> Upload Document</h3>
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="file-upload" className="btn btn-primary"
          style={{ cursor: uploading ? 'not-allowed' : 'pointer', opacity: uploading ? 0.6 : 1 }}>
          <File size={18} />
          {uploading ? 'Uploading...' : 'Choose File (PDF, DOCX, TXT)'}
        </label>
        <input id="file-upload" ref={inputRef} type="file" accept=".pdf,.docx,.txt"
          onChange={handleFileChange} disabled={uploading} style={{ display: 'none' }} />
      </div>
      {message && (
        <div style={{ background: 'rgba(16,185,129,0.1)', color: '#34d399', padding: '10px 14px', borderRadius: 8, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8, border: '1px solid rgba(16,185,129,0.2)', fontSize: '0.9rem' }}>
          <CheckCircle size={18} /> {message}
        </div>
      )}
      {error && <div className="error"><AlertCircle size={18} /> {error}</div>}
      <p style={{ fontSize: '0.85rem', color: '#475569', marginTop: 8 }}>PDF, DOCX, TXT — max 10MB</p>
    </div>
  )
}
