'use client'

import { useState } from 'react'
import { ExternalLink, BookOpen, Globe, Save, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { useSaveWebResultMutation } from '@/store/api/devflowApi'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import type { HybridSearchResult, WebResult } from '@/types'

export default function ResultCard({ result }: { result: HybridSearchResult }) {
  const [savedUrls, setSavedUrls] = useState<Set<string>>(new Set())
  const [saveWebResult] = useSaveWebResultMutation()

  const handleSave = async (wr: WebResult) => {
    try {
      await saveWebResult({ title: wr.title, url: wr.url, content: wr.content }).unwrap()
      setSavedUrls((prev) => new Set(Array.from(prev).concat(wr.url)))
    } catch {
      toast.error('Failed to save result')
    }
  }

  const docSources = result.doc_sources || []
  const webSources = result.web_sources || []
  const webResultsFull = result.web_results_full || []

  return (
    <div className="result-card">
      <div className="result-header">
        <h3>
          Answer
          {result.cached && <span className="cached-badge">⚡ Cached</span>}
        </h3>
      </div>
      <div className="result-content">
        <MarkdownRenderer content={result.answer || ''} />
      </div>

      {docSources.length > 0 && (
        <div className="sources-section">
          <h4><BookOpen size={18} /> From Your Documents ({docSources.length})</h4>
          <div className="sources-list">
            {docSources.map((src, i) => (
              <div key={i} className="source-item">
                <span className="source-title">{src.title || src.url}</span>
                {src.url && src.url !== 'manual' && (
                  <a href={src.url} target="_blank" rel="noopener noreferrer" className="source-link">
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {webResultsFull.length > 0 && (
        <div className="sources-section" style={{ marginTop: 24 }}>
          <h4><Globe size={18} /> From the Web ({webSources.length})</h4>
          <div className="sources-list">
            {webResultsFull.map((wr, i) => {
              const saved = savedUrls.has(wr.url)
              return (
                <div key={i} className="source-item web-source">
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500, marginBottom: 4, color: '#e2e8f0' }}>{wr.title}</div>
                    <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: 6 }}>{wr.description}</div>
                    <a href={wr.url} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: '0.82rem', color: '#818cf8', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
                      {wr.url} <ExternalLink size={12} />
                    </a>
                  </div>
                  {saved ? (
                    <button className="btn btn-success" disabled style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 90 }}>
                      <CheckCircle size={16} /> Saved
                    </button>
                  ) : (
                    <button className="btn btn-primary" onClick={() => handleSave(wr)}
                      style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 90 }}>
                      <Save size={16} /> Save
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {docSources.length === 0 && webSources.length === 0 && (
        <div className="empty-state" style={{ marginTop: 20, padding: '24px 0' }}>
          <p>No sources available</p>
        </div>
      )}
    </div>
  )
}
