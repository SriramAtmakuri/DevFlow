export interface Source {
  id: number
  type: string
  name: string | null
  path: string | null
  status: string
  indexed_at: string | null
  created_at: string
  doc_count: number
}

export interface SourceMeta {
  title: string
  url?: string
  source_type?: string
  chunk_index?: number
}

export interface WebResult {
  title: string
  url: string
  description: string
  content: string
}

export interface WebSource {
  title: string
  url: string
  source: string
}

export interface SearchResult {
  answer: string
  sources: SourceMeta[]
  query: string
  model: string
  cached: boolean
}

export interface HybridSearchResult {
  answer: string
  doc_sources: SourceMeta[]
  web_sources: WebSource[]
  web_results_full: WebResult[]
  query: string
  cached: boolean
}

export interface Stats {
  sources: number
  documents: number
  searches: number
  chromadb_count: number
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: number
  username: string
}

export interface Collection {
  id: number
  name: string
  description: string | null
  source_count: number
  created_at: string
}

export interface HistoryItem {
  id: number
  query: string
  results_count: number
  cached: number
  model: string
  created_at: string
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'indexing' | 'completed' | 'failed'
  filename: string
  chunks: number
  error: string | null
}

export interface SourceChunk {
  id: string
  text: string
  chunk_index: number
  total_chunks: number
}

export interface AnalyticsData {
  cache_hit_rate: number
  chromadb_count: number
  top_queries: { query: string; count: number }[]
  searches_by_day: { date: string; count: number; cache_hits: number }[]
  source_types: { type: string; count: number }[]
  model_usage: { model: string; count: number }[]
}
