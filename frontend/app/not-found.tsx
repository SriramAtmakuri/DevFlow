import Link from 'next/link'
import { Brain, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 20,
      background: '#0f172a', color: '#e2e8f0', padding: 32, textAlign: 'center',
    }}>
      <Brain size={52} style={{ color: '#818cf8', opacity: 0.6 }} />
      <h1 style={{ fontSize: '5rem', fontWeight: 800, color: '#818cf8', margin: 0, lineHeight: 1 }}>404</h1>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>Page not found</h2>
      <p style={{ color: '#64748b', margin: 0 }}>That page doesn&apos;t exist in your knowledge base.</p>
      <Link href="/search" style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 20px', borderRadius: 8,
        background: 'linear-gradient(135deg,#667eea,#764ba2)', color: 'white',
        textDecoration: 'none', fontWeight: 500, marginTop: 8,
      }}>
        <ArrowLeft size={16} /> Back to Search
      </Link>
    </div>
  )
}
