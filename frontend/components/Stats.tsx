'use client'

import { useGetStatsQuery } from '@/store/api/devflowApi'

export default function Stats() {
  const { data: stats } = useGetStatsQuery()
  if (!stats) return null

  const items = [
    { label: 'Sources', value: stats.sources },
    { label: 'Documents', value: stats.documents },
    { label: 'Searches', value: stats.searches },
    { label: 'Vectors', value: stats.chromadb_count },
  ]

  return (
    <div className="stats">
      {items.map(({ label, value }) => (
        <div key={label} className="stat-card">
          <div className="stat-value">{value}</div>
          <div className="stat-label">{label}</div>
        </div>
      ))}
    </div>
  )
}
