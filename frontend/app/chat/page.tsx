'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Plus, Bot, User, Zap } from 'lucide-react'
import Navbar from '@/components/Navbar'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import { useSelector } from 'react-redux'
import type { RootState } from '@/store'
import { useGetCollectionsQuery } from '@/store/api/devflowApi'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const MODELS = [
  { value: 'gemini-flash', label: 'Gemini Flash' },
  { value: 'gemini-pro', label: 'Gemini Pro' },
  { value: 'claude-haiku', label: 'Claude Haiku' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
]

interface Message { role: 'user' | 'assistant'; content: string }

export default function ChatPage() {
  const { token } = useSelector((s: RootState) => s.auth)
  const { data: collectionsData } = useGetCollectionsQuery()
  const [collectionId, setCollectionId] = useState<string>('')
  const [useHyde, setUseHyde] = useState(false)
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === 'undefined') return []
    try {
      const saved = localStorage.getItem('devflow_chat')
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [model, setModel] = useState('gemini-flash')
  const [useWeb, setUseWeb] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!streaming) {
      try { localStorage.setItem('devflow_chat', JSON.stringify(messages)) } catch { /* quota */ }
    }
  }, [messages, streaming])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || streaming) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setStreaming(true)

    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const res = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: msg,
          session_id: sessionId,
          model,
          use_web: useWeb,
          use_hyde: useHyde,
          collection_id: collectionId ? Number(collectionId) : undefined,
        }),
      })

      if (!res.body) throw new Error('No stream')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let answer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const lines = decoder.decode(value, { stream: true }).split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') break
          try {
            const { chunk } = JSON.parse(data)
            if (chunk) {
              answer += chunk
              setMessages(prev => {
                const copy = [...prev]
                copy[copy.length - 1] = { role: 'assistant', content: answer }
                return copy
              })
            }
          } catch { /* partial chunk */ }
        }
      }
    } catch (e: unknown) {
      const err = e as Error
      setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = { role: 'assistant', content: `Error: ${err.message}` }
        return copy
      })
    } finally {
      setStreaming(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="container" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar active="chat" />

      {/* Controls bar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <select value={model} onChange={e => setModel(e.target.value)}
          style={{ padding: '8px 14px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, color: '#e2e8f0', fontSize: '0.9rem', cursor: 'pointer' }}>
          {MODELS.map(m => <option key={m.value} value={m.value} style={{ background: '#1e293b' }}>{m.label}</option>)}
        </select>

        <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: '0.9rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={useWeb} onChange={e => setUseWeb(e.target.checked)} />
          Web fallback
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: '0.9rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={useHyde} onChange={e => setUseHyde(e.target.checked)} />
          HyDE retrieval
        </label>

        {collectionsData?.collections?.length ? (
          <select value={collectionId} onChange={e => setCollectionId(e.target.value)}
            style={{ padding: '8px 14px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, color: '#e2e8f0', fontSize: '0.9rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
            <option value="" style={{ background: '#1e293b' }}>All sources</option>
            {collectionsData.collections.map(c => (
              <option key={c.id} value={c.id} style={{ background: '#1e293b' }}>{c.name}</option>
            ))}
          </select>
        ) : null}

        <button onClick={() => { setMessages([]); localStorage.removeItem('devflow_chat') }} className="btn"
          style={{ marginLeft: 'auto', padding: '8px 14px', background: 'rgba(255,255,255,0.06)', color: '#94a3b8', border: '1px solid rgba(255,255,255,0.1)', fontSize: '0.85rem' }}>
          <Plus size={14} /> New chat
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', marginBottom: 16, minHeight: 300 }}>
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon"><Bot size={56} style={{ opacity: 0.25 }} /></div>
            <h3>Start a conversation</h3>
            <p>Ask follow-up questions — context is remembered across turns.</p>
          </div>
        )}
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: msg.role === 'user' ? 'linear-gradient(135deg,#667eea,#764ba2)' : 'rgba(255,255,255,0.08)' }}>
                {msg.role === 'user' ? <User size={16} color="white" /> : <Bot size={16} color="#818cf8" />}
              </div>
              <div style={{ maxWidth: '75%', background: msg.role === 'user' ? 'rgba(102,126,234,0.15)' : 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '12px 16px' }}>
                {msg.role === 'assistant' ? (
                  <>
                    <MarkdownRenderer content={msg.content || '...'} />
                    {streaming && i === messages.length - 1 && !msg.content && (
                      <span style={{ color: '#818cf8', animation: 'pulse 1s infinite' }}>●</span>
                    )}
                  </>
                ) : (
                  <p style={{ color: '#e2e8f0', margin: 0 }}>{msg.content}</p>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 10, position: 'sticky', bottom: 20 }}>
        <textarea
          rows={1}
          className="search-input"
          style={{ resize: 'none', minHeight: 48, lineHeight: '1.5' }}
          placeholder="Ask a follow-up question... (Enter to send, Shift+Enter for newline)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={streaming}
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={streaming || !input.trim()}
          style={{ alignSelf: 'flex-end', padding: '12px 20px' }}>
          {streaming ? <Zap size={20} /> : <Send size={20} />}
        </button>
      </div>
    </div>
  )
}
