'use client'

import { motion } from 'framer-motion'
import Navbar from '@/components/Navbar'
import { useGetAnalyticsQuery } from '@/store/api/devflowApi'
import type { AnalyticsData } from '@/types'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

const COLORS = ['#818cf8', '#a78bfa', '#f472b6', '#34d399', '#fb923c']

export default function AnalyticsPage() {
  const { data, isLoading } = useGetAnalyticsQuery()

  if (isLoading) return (
    <div className="container"><Navbar active="analytics" /><div className="loading">Loading analytics</div></div>
  )

  const d = data as AnalyticsData

  return (
    <div className="container">
      <Navbar active="analytics" />
      <div className="header">
        <h1>Analytics</h1>
        <p>Query patterns, cache performance, model usage</p>
      </div>
      <div className="main-content">

        {/* KPI row */}
        <div className="stats" style={{ marginBottom: 40 }}>
          {[
            { label: 'Cache Hit Rate', value: `${d?.cache_hit_rate ?? 0}%` },
            { label: 'Vector Chunks', value: d?.chromadb_count ?? 0 },
          ].map((k, i) => (
            <motion.div key={k.label} className="stat-card"
              initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.1, ease: [0.25,0.1,0.25,1] }}>
              <div className="stat-value">{k.value}</div>
              <div className="stat-label">{k.label}</div>
            </motion.div>
          ))}
        </div>

        <motion.div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 28 }}
          initial="hidden" animate="show" variants={{ hidden: {}, show: { transition: { staggerChildren: 0.1 } } }}>

          {/* Searches per day */}
          <motion.div variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.32 } } }} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: 24, border: '1px solid rgba(255,255,255,0.08)' }}>
            <h3 style={{ color: '#e2e8f0', marginBottom: 20 }}>Searches per Day</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={d?.searches_by_day || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e2e8f0' }} />
                <Line type="monotone" dataKey="count" stroke="#818cf8" strokeWidth={2} dot={{ fill: '#818cf8', r: 3 }} name="Searches" />
                <Line type="monotone" dataKey="cache_hits" stroke="#34d399" strokeWidth={2} dot={{ fill: '#34d399', r: 3 }} name="Cache hits" />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Top queries */}
          <motion.div variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.32 } } }} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: 24, border: '1px solid rgba(255,255,255,0.08)' }}>
            <h3 style={{ color: '#e2e8f0', marginBottom: 20 }}>Top Queries</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={(d?.top_queries || []).slice(0, 6)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis type="category" dataKey="query" width={120}
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  tickFormatter={(v: string) => v.length > 18 ? v.slice(0, 18) + '…' : v} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e2e8f0' }} />
                <Bar dataKey="count" fill="#818cf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Source types */}
          {d?.source_types?.length > 0 && (
            <motion.div variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.32 } } }} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: 24, border: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ color: '#e2e8f0', marginBottom: 20 }}>Source Types</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={d.source_types} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={70} label={({ type, percent }: { type: string; percent: number }) => `${type} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}>
                    {d.source_types.map((_entry, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e2e8f0' }} />
                </PieChart>
              </ResponsiveContainer>
            </motion.div>
          )}

          {/* Model usage */}
          {d?.model_usage?.length > 0 && (
            <motion.div variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0, transition: { duration: 0.32 } } }} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: 24, border: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ color: '#e2e8f0', marginBottom: 20 }}>Model Usage</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={d.model_usage}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="model" tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e2e8f0' }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {d.model_usage.map((_entry, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </motion.div>
          )}

        </motion.div>
      </div>
    </div>
  )
}
