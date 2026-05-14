import type { Metadata } from 'next'
import './globals.css'
import Providers from '@/components/Providers'
import ErrorBoundary from '@/components/ErrorBoundary'

export const metadata: Metadata = {
  title: 'DevFlow — AI Knowledge Base',
  description: 'Production RAG-based coding knowledge base',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers><ErrorBoundary>{children}</ErrorBoundary></Providers>
      </body>
    </html>
  )
}
