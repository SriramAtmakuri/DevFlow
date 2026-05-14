'use client'

import { useState } from 'react'
import { Search, Globe } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string, useWeb: boolean) => void
  loading: boolean
}

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [useWeb, setUseWeb] = useState(true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) onSearch(query.trim(), useWeb)
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
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, cursor: 'pointer', fontSize: '0.9rem', color: '#64748b' }}>
        <input type="checkbox" checked={useWeb} onChange={(e) => setUseWeb(e.target.checked)} style={{ cursor: 'pointer' }} />
        <Globe size={16} />
        Search web if not in my documents
      </label>
    </div>
  )
}
