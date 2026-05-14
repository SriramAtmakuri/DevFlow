'use client'

import { useState } from 'react'
import { Search, Globe, Zap } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string, useWeb: boolean, useHyde: boolean) => void
  loading: boolean
}

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [useWeb, setUseWeb] = useState(true)
  const [useHyde, setUseHyde] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSearch(query.trim(), useWeb, useHyde)
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="search-box">
        <input
          type="text"
          className="search-input"
          placeholder="Ask anything about coding..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !query.trim()}>
          <Search size={20} />
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      <div style={{ display: 'flex', gap: 20, marginTop: 12, flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.9rem', color: '#64748b' }}>
          <input type="checkbox" checked={useWeb} onChange={(e) => setUseWeb(e.target.checked)} style={{ cursor: 'pointer' }} />
          <Globe size={15} />
          Web fallback
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.9rem', color: '#64748b' }}>
          <input type="checkbox" checked={useHyde} onChange={(e) => setUseHyde(e.target.checked)} style={{ cursor: 'pointer' }} />
          <Zap size={15} />
          HyDE retrieval
        </label>
      </div>
    </div>
  )
}
