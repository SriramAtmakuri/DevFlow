'use client'

import { useState } from 'react'
import { motion, AnimatePresence, type Variants } from 'framer-motion'
import { Plus, Trash2, FolderOpen } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  useGetSourcesQuery,
  useDeleteSourceMutation,
  useAddManualDocumentMutation,
} from '@/store/api/devflowApi'
import FileUpload from './FileUpload'
import { SkeletonList } from './SkeletonCard'

const listVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}
const itemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.28, ease: 'easeOut' } },
}

export default function SourceManager() {
  const { data, isLoading } = useGetSourcesQuery()
  const [deleteSource] = useDeleteSourceMutation()
  const [addManual, { isLoading: adding }] = useAddManualDocumentMutation()
  const [form, setForm] = useState({ title: '', content: '', url: '' })

  const sources = data?.sources || []

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await addManual({ title: form.title, content: form.content, url: form.url || undefined }).unwrap()
      setForm({ title: '', content: '', url: '' })
      toast.success('Document added!')
    } catch {
      toast.error('Failed to add document')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this source?')) return
    try {
      await deleteSource(id).unwrap()
      toast.success('Source deleted')
    } catch {
      toast.error('Failed to delete source')
    }
  }

  return (
    <div>
      <FileUpload />

      <div style={{ height: 2, background: 'linear-gradient(to right, rgba(255,255,255,0.1), transparent)', margin: '30px 0' }} />

      <div className="add-source-form">
        <h3>Add Manually</h3>
        <form onSubmit={handleAdd}>
          <div className="form-group">
            <label>Title</label>
            <input type="text" placeholder="Document title" value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })} required disabled={adding} />
          </div>
          <div className="form-group">
            <label>Content</label>
            <textarea rows={6} placeholder="Paste your content here..." value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })} required disabled={adding} />
          </div>
          <div className="form-group">
            <label>URL (optional)</label>
            <input type="text" placeholder="https://example.com" value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })} disabled={adding} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={adding}>
            <Plus size={18} />{adding ? 'Adding...' : 'Add Document'}
          </button>
        </form>
      </div>

      <h3 style={{ marginTop: 40, marginBottom: 20, color: '#e2e8f0' }}>Your Sources ({sources.length})</h3>
      {isLoading ? (
        <SkeletonList count={3} />
      ) : sources.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon"><FolderOpen size={52} /></span>
          <p>No sources yet. Upload a file or add a document above.</p>
        </div>
      ) : (
        <motion.div className="sources-list" variants={listVariants} initial="hidden" animate="show">
          <AnimatePresence mode="popLayout">
            {sources.map((src) => (
              <motion.div key={src.id} className="source-card" variants={itemVariants} layout exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.2 } }}>
                <div className="source-info">
                  <h4>{src.name || src.type}</h4>
                  <p>
                    <span className="badge badge-success">{src.status}</span>
                    {src.doc_count} chunk{src.doc_count !== 1 ? 's' : ''}
                  </p>
                </div>
                <button className="btn btn-danger" onClick={() => handleDelete(src.id)}>
                  <Trash2 size={16} /> Delete
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  )
}
