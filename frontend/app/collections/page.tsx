'use client'

import { useState } from 'react'
import { motion, AnimatePresence, type Variants } from 'framer-motion'
import { Plus, Trash2, FolderOpen, Folder } from 'lucide-react'
import toast from 'react-hot-toast'
import Navbar from '@/components/Navbar'
import {
  useGetCollectionsQuery,
  useCreateCollectionMutation,
  useDeleteCollectionMutation,
} from '@/store/api/devflowApi'
import { SkeletonList } from '@/components/SkeletonCard'
import type { Collection } from '@/types'

const listVariants: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } }
const itemVariants: Variants = { hidden: { opacity: 0, scale: 0.97 }, show: { opacity: 1, scale: 1, transition: { duration: 0.28, ease: 'easeOut' } } }

export default function CollectionsPage() {
  const { data, isLoading } = useGetCollectionsQuery()
  const [createCollection, { isLoading: creating }] = useCreateCollectionMutation()
  const [deleteCollection] = useDeleteCollectionMutation()
  const [form, setForm] = useState({ name: '', description: '' })

  const collections: Collection[] = data?.collections || []

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createCollection({ name: form.name, description: form.description || undefined }).unwrap()
      setForm({ name: '', description: '' })
      toast.success('Collection created!')
    } catch { toast.error('Failed to create collection') }
  }

  return (
    <div className="container">
      <Navbar active="collections" />
      <div className="header">
        <h1>Collections</h1>
        <p>Organise sources into workspaces</p>
      </div>
      <div className="main-content">

        <div className="add-source-form">
          <h3>New Collection</h3>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Name</label>
              <input type="text" placeholder="e.g. React Docs" value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })} required disabled={creating} />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input type="text" placeholder="What this collection is for" value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })} disabled={creating} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              <Plus size={18} />{creating ? 'Creating...' : 'Create Collection'}
            </button>
          </form>
        </div>

        <h3 style={{ color: '#e2e8f0', marginBottom: 20 }}>Your Collections ({collections.length})</h3>
        {isLoading ? <SkeletonList count={3} />
          : collections.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state-icon"><FolderOpen size={48} /></span>
              <p>No collections yet. Create one above.</p>
            </div>
          ) : (
            <motion.div className="sources-list" variants={listVariants} initial="hidden" animate="show">
              <AnimatePresence mode="popLayout">
              {collections.map((col) => (
                <motion.div key={col.id} className="source-card" variants={itemVariants} layout exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.18 } }}>
                  <div className="source-info" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Folder size={20} style={{ color: '#818cf8', flexShrink: 0 }} />
                    <div>
                      <h4>{col.name}</h4>
                      <p>{col.description && <span style={{ marginRight: 10 }}>{col.description}</span>}
                        <span className="badge badge-success">{col.source_count} sources</span>
                      </p>
                    </div>
                  </div>
                  <button className="btn btn-danger" onClick={() => deleteCollection(col.id).catch(() => toast.error('Failed to delete'))}>
                    <Trash2 size={16} /> Delete
                  </button>
                </motion.div>
              ))}
              </AnimatePresence>
            </motion.div>
          )}
      </div>
    </div>
  )
}
