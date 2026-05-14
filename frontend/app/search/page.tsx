'use client'

import { useState } from 'react'
import { Brain } from 'lucide-react'
import SearchBar from '@/components/SearchBar'
import ResultCard from '@/components/ResultCard'
import Navbar from '@/components/Navbar'
import { useHybridSearchMutation } from '@/store/api/devflowApi'
import type { HybridSearchResult } from '@/types'

export default function SearchPage() {
  const [result, setResult] = useState<HybridSearchResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hybridSearch, { isLoading }] = useHybridSearchMutation()

  const handleSearch = async (query: string, useWeb: boolean) => {
    setError(null)
    setResult(null)
    try {
      const data = await hybridSearch({ query, use_web: useWeb }).unwrap()
      setResult(data)
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } }
      setError(e?.data?.detail || 'Search failed')
    }
  }

  return (
    <div className="container">
      <Navbar active="search" />
      <div className="header">
        <h1><Brain size={44} />DevFlow</h1>
        <p>Your Personal Coding Knowledge Base</p>
      </div>
      <div className="main-content">
        <SearchBar onSearch={handleSearch} loading={isLoading} />
        {error && <div className="error">{error}</div>}
        {isLoading && <div className="loading">Searching knowledge base...</div>}
        {result && !isLoading && <ResultCard result={result} />}
        {!result && !isLoading && !error && (
          <div className="empty-state">
            <div className="empty-state-icon">💡</div>
            <h3>Ask me anything!</h3>
            <p>Search through your saved coding resources, powered by semantic AI.</p>
          </div>
        )}
      </div>
    </div>
  )
}
