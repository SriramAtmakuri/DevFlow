'use client'

import { motion, type Variants } from 'framer-motion'
import { Clock, Search, Zap } from 'lucide-react'
import Navbar from '@/components/Navbar'
import { useGetHistoryQuery } from '@/store/api/devflowApi'
import { SkeletonList } from '@/components/SkeletonCard'
import type { HistoryItem } from '@/types'

const listVariants: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } }
const itemVariants: Variants = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0, transition: { duration: 0.26, ease: 'easeOut' } } }

export default function HistoryPage() {
  const { data, isLoading } = useGetHistoryQuery()
  const history: HistoryItem[] = data?.history || []

  return (
    <div className="container">
      <Navbar active="history" />
      <div className="header">
        <h1>Search History</h1>
        <p>Your past queries and results</p>
      </div>
      <div className="main-content">
        {isLoading && <SkeletonList count={5} />}
        {!isLoading && history.length === 0 && (
          <div className="empty-state">
            <span className="empty-state-icon"><Clock size={52} /></span>
            <p>No searches yet. Start asking questions!</p>
          </div>
        )}
        <motion.div className="sources-list" variants={listVariants} initial="hidden" animate="show">
          {history.map((item) => (
            <motion.div key={item.id} className="source-card" variants={itemVariants} style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}>
                <Search size={15} style={{ color: 'var(--clr-brand-1)', flexShrink: 0 }} />
                <span style={{ color: '#e2e8f0', fontWeight: 500, flex: 1, fontSize: '0.95rem' }}>{item.query}</span>
                {item.cached === 1 && <span className="cached-badge"><Zap size={12} /> Cached</span>}
                <span className="badge" style={{ background: 'rgba(139,124,248,0.1)', color: 'var(--clr-brand-1)' }}>{item.model}</span>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: '0.8rem', color: '#475569' }}>
                <span>{item.results_count} results</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
