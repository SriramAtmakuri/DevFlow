'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '')
          const isBlock = !props.inline && match
          return isBlock ? (
            <SyntaxHighlighter
              style={oneDark as any}
              language={match[1]}
              PreTag="div"
              customStyle={{ borderRadius: 8, fontSize: '0.88rem', margin: '12px 0' }}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code
              style={{
                background: 'rgba(255,255,255,0.08)',
                padding: '2px 6px',
                borderRadius: 4,
                fontSize: '0.88em',
                fontFamily: 'monospace',
              }}
              {...props}
            >
              {children}
            </code>
          )
        },
        p: ({ children }) => (
          <p style={{ marginBottom: 12, lineHeight: 1.75, color: '#cbd5e1' }}>{children}</p>
        ),
        h1: ({ children }) => (
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#e2e8f0', margin: '20px 0 10px' }}>{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#e2e8f0', margin: '16px 0 8px' }}>{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#94a3b8', margin: '12px 0 6px' }}>{children}</h3>
        ),
        ul: ({ children }) => (
          <ul style={{ paddingLeft: 20, marginBottom: 12, color: '#cbd5e1' }}>{children}</ul>
        ),
        ol: ({ children }) => (
          <ol style={{ paddingLeft: 20, marginBottom: 12, color: '#cbd5e1' }}>{children}</ol>
        ),
        li: ({ children }) => <li style={{ marginBottom: 4 }}>{children}</li>,
        blockquote: ({ children }) => (
          <blockquote style={{
            borderLeft: '3px solid #818cf8', paddingLeft: 16, margin: '12px 0',
            color: '#94a3b8', fontStyle: 'italic',
          }}>{children}</blockquote>
        ),
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer"
            style={{ color: '#818cf8', textDecoration: 'underline' }}>{children}</a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
