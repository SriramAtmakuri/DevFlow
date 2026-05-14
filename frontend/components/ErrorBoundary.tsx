'use client'

import { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props { children: ReactNode }
interface State { error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 16,
          background: '#0f172a', color: '#e2e8f0', padding: 32,
        }}>
          <AlertTriangle size={48} color="#f87171" />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#f87171' }}>Something went wrong</h2>
          <pre style={{
            background: 'rgba(255,255,255,0.05)', borderRadius: 8,
            padding: '12px 16px', fontSize: '0.82rem', color: '#94a3b8',
            maxWidth: 600, overflowX: 'auto', whiteSpace: 'pre-wrap',
          }}>
            {this.state.error.message}
          </pre>
          <button
            onClick={() => { this.setState({ error: null }); window.location.reload() }}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg,#667eea,#764ba2)', color: 'white', fontWeight: 500,
            }}
          >
            <RefreshCw size={16} /> Reload page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
