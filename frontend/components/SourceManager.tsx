'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence, type Variants } from 'framer-motion'
import { Plus, Trash2, FolderOpen, Link, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, Loader, CheckSquare, Square } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  useGetSourcesQuery,
  useDeleteSourceMutation,
  useAddManualDocumentMutation,
  useIndexUrlMutation,
  useBulkDeleteSourcesMutation,
  useGetSourceChunksQuery,
  useGetJobStatusQuery,
  useGetCollectionsQuery,
} from '@/store/api/devflowApi'
import type { SourceChunk } from '@/types'
import FileUpload from './FileUpload'
import { SkeletonList } from './SkeletonCard'

const PAGE_SIZE = 10

const listVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05 } },
}
const itemVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.26, ease: 'easeOut' } },
}

function ChunkPreview({ sourceId }: { sourceId: number }) {
  const { data, isLoading } = useGetSourceChunksQuery(sourceId)
  const chunks: SourceChunk[] = data?.chunks || []

  if (isLoading) return (
    <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.07)', color: '#64748b', fontSize: '0.85rem' }}>
      Loading chunks…
    </div>
  )

  return (
    <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.07)', background: 'rgba(0,0,0,0.15)' }}>
      <p style={{ fontSize: '0.78rem', color: '#475569', marginBottom: 10 }}>{chunks.length} chunks indexed</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 260, overflowY: 'auto' }}>
        {chunks.map((chunk) => (
          <div key={chunk.id} style={{ fontSize: '0.81rem', color: '#94a3b8', background: 'rgba(255,255,255,0.03)', borderRadius: 6, padding: '7px 10px', lineHeight: 1.55 }}>
            <span style={{ fontSize: '0.7rem', color: '#475569', marginRight: 6 }}>#{chunk.chunk_index + 1}</span>
            {chunk.text.slice(0, 220)}{chunk.text.length > 220 ? '…' : ''}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function SourceManager() {
  const { data, isLoading, refetch: refetchSources } = useGetSourcesQuery()
  const { data: collectionsData } = useGetCollectionsQuery()
  const [deleteSource] = useDeleteSourceMutation()
  const [addManual, { isLoading: adding }] = useAddManualDocumentMutation()
  const [indexUrl] = useIndexUrlMutation()
  const [bulkDelete, { isLoading: bulkDeleting }] = useBulkDeleteSourcesMutation()

  const [manualForm, setManualForm] = useState({ title: '', content: '', url: '' })
  const [urlForm, setUrlForm] = useState({ url: '', title: '', collectionId: '' })
  const [urlJobId, setUrlJobId] = useState<string | null>(null)

  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [page, setPage] = useState(0)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data: urlJobData } = useGetJobStatusQuery(urlJobId!, {
    skip: !urlJobId,
    pollingInterval: urlJobId ? 2000 : 0,
  })

  useEffect(() => {
    if (!urlJobData) return
    if (urlJobData.status === 'completed') {
      setUrlJobId(null)
      toast.success(`URL indexed — ${urlJobData.chunks} chunks`)
      refetchSources()
      setPage(0)
    } else if (urlJobData.status === 'failed') {
      setUrlJobId(null)
      toast.error(urlJobData.error || 'URL indexing failed')
    }
  }, [urlJobData?.status])

  const sources = data?.sources || []
  const totalPages = Math.ceil(sources.length / PAGE_SIZE)
  const pageSources = sources.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const collections = collectionsData?.collections || []

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await addManual({ title: manualForm.title, content: manualForm.content, url: manualForm.url || undefined }).unwrap()
      setManualForm({ title: '', content: '', url: '' })
      toast.success('Document added!')
    } catch { toast.error('Failed to add document') }
  }

  const handleIndexUrl = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await indexUrl({
        url: urlForm.url,
        title: urlForm.title || undefined,
        collection_id: urlForm.collectionId ? Number(urlForm.collectionId) : undefined,
      }).unwrap()
      setUrlJobId(res.job_id)
      setUrlForm({ url: '', title: '', collectionId: '' })
      toast.success('URL queued for indexing…')
    } catch { toast.error('Failed to queue URL') }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this source?')) return
    try {
      await deleteSource(id).unwrap()
      setSelected(prev => { const s = new Set(prev); s.delete(id); return s })
      toast.success('Source deleted')
    } catch { toast.error('Failed to delete source') }
  }

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${selected.size} source${selected.size > 1 ? 's' : ''}?`)) return
    try {
      await bulkDelete({ ids: Array.from(selected) }).unwrap()
      setSelected(new Set())
      setPage(0)
      toast.success(`Deleted ${selected.size} sources`)
    } catch { toast.error('Bulk delete failed') }
  }

  const toggleSelect = (id: number) => {
    setSelected(prev => {
      const s = new Set(prev)
      s.has(id) ? s.delete(id) : s.add(id)
      return s
    })
  }

  const toggleSelectAll = () => {
    if (pageSources.every(s => selected.has(s.id))) {
      setSelected(prev => { const s = new Set(prev); pageSources.forEach(src => s.delete(src.id)); return s })
    } else {
      setSelected(prev => { const s = new Set(prev); pageSources.forEach(src => s.add(src.id)); return s })
    }
  }

  const isIndexingUrl = !!urlJobId
  const allPageSelected = pageSources.length > 0 && pageSources.every(s => selected.has(s.id))

  return (
    <div>
      <FileUpload />

      <div style={{ height: 2, background: 'linear-gradient(to right, rgba(255,255,255,0.1), transparent)', margin: '30px 0' }} />

      {/* URL Indexing */}
      <div className="add-source-form">
        <h3><Link size={16} style={{ display: 'inline', marginRight: 8 }} />Index a URL</h3>
        <form onSubmit={handleIndexUrl}>
          <div className="form-group">
            <label>URL</label>
            <input type="url" placeholder="https://docs.example.com/guide" value={urlForm.url}
              onChange={e => setUrlForm({ ...urlForm, url: e.target.value })} required disabled={isIndexingUrl} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group">
              <label>Title (optional)</label>
              <input type="text" placeholder="Auto-detected if blank" value={urlForm.title}
                onChange={e => setUrlForm({ ...urlForm, title: e.target.value })} disabled={isIndexingUrl} />
            </div>
            <div className="form-group">
              <label>Collection (optional)</label>
              <select value={urlForm.collectionId} onChange={e => setUrlForm({ ...urlForm, collectionId: e.target.value })}
                disabled={isIndexingUrl}
                style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.05)', border: '1.5px solid rgba(255,255,255,0.1)', borderRadius: 'var(--radius-md)', color: '#e2e8f0', width: '100%' }}>
                <option value="">None</option>
                {collections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={isIndexingUrl}>
            {isIndexingUrl
              ? <><Loader size={16} style={{ animation: 'spin 1s linear infinite' }} /> Indexing…</>
              : <><Link size={16} /> Index URL</>}
          </button>
        </form>
      </div>

      <div style={{ height: 2, background: 'linear-gradient(to right, rgba(255,255,255,0.1), transparent)', margin: '30px 0' }} />

      {/* Manual Add */}
      <div className="add-source-form">
        <h3>Add Manually</h3>
        <form onSubmit={handleAdd}>
          <div className="form-group">
            <label>Title</label>
            <input type="text" placeholder="Document title" value={manualForm.title}
              onChange={e => setManualForm({ ...manualForm, title: e.target.value })} required disabled={adding} />
          </div>
          <div className="form-group">
            <label>Content</label>
            <textarea rows={6} placeholder="Paste your content here…" value={manualForm.content}
              onChange={e => setManualForm({ ...manualForm, content: e.target.value })} required disabled={adding} />
          </div>
          <div className="form-group">
            <label>URL (optional)</label>
            <input type="text" placeholder="https://example.com" value={manualForm.url}
              onChange={e => setManualForm({ ...manualForm, url: e.target.value })} disabled={adding} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={adding}>
            <Plus size={18} />{adding ? 'Adding…' : 'Add Document'}
          </button>
        </form>
      </div>

      {/* Sources list */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 40, marginBottom: 20 }}>
        <h3 style={{ color: '#e2e8f0' }}>Your Sources ({sources.length})</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {selected.size > 0 && (
            <button className="btn btn-danger" onClick={handleBulkDelete} disabled={bulkDeleting}
              style={{ padding: '7px 14px', fontSize: '0.85rem' }}>
              <Trash2 size={14} /> Delete {selected.size}
            </button>
          )}
          {sources.length > 0 && (
            <button onClick={toggleSelectAll}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.85rem' }}>
              {allPageSelected ? <CheckSquare size={16} color="#818cf8" /> : <Square size={16} />}
              {allPageSelected ? 'Deselect page' : 'Select page'}
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <SkeletonList count={3} />
      ) : sources.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon"><FolderOpen size={52} /></span>
          <p>No sources yet. Upload a file, index a URL, or add a document above.</p>
        </div>
      ) : (
        <>
          <motion.div className="sources-list" variants={listVariants} initial="hidden" animate="show">
            <AnimatePresence mode="popLayout">
              {pageSources.map((src) => {
                const isExpanded = expandedId === src.id
                const isChecked = selected.has(src.id)
                return (
                  <motion.div key={src.id} className="source-card" variants={itemVariants} layout
                    exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.18 } }}
                    style={{ flexDirection: 'column', alignItems: 'stretch', padding: 0, overflow: 'hidden' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px' }}>
                      <button onClick={() => toggleSelect(src.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: isChecked ? '#818cf8' : '#475569', flexShrink: 0, display: 'flex' }}>
                        {isChecked ? <CheckSquare size={18} /> : <Square size={18} />}
                      </button>
                      <div className="source-info" style={{ flex: 1 }}>
                        <h4>{src.name || src.type}</h4>
                        <p>
                          <span className="badge badge-success">{src.status}</span>
                          {src.doc_count} chunk{src.doc_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <button onClick={() => setExpandedId(isExpanded ? null : src.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#475569', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem' }}>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                      <button className="btn btn-danger" onClick={() => handleDelete(src.id)}
                        style={{ padding: '6px 12px', fontSize: '0.82rem' }}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22, ease: 'easeOut' }}>
                          <ChunkPreview sourceId={src.id} />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </motion.div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 24 }}>
              <button className="btn" onClick={() => setPage(p => p - 1)} disabled={page === 0}
                style={{ padding: '7px 14px', background: 'rgba(255,255,255,0.05)', color: '#94a3b8', border: '1px solid rgba(255,255,255,0.1)' }}>
                <ChevronLeft size={16} />
              </button>
              <span style={{ color: '#64748b', fontSize: '0.9rem' }}>
                {page + 1} / {totalPages}
              </span>
              <button className="btn" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}
                style={{ padding: '7px 14px', background: 'rgba(255,255,255,0.05)', color: '#94a3b8', border: '1px solid rgba(255,255,255,0.1)' }}>
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
