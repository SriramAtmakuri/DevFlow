'use client'

import Navbar from '@/components/Navbar'
import Stats from '@/components/Stats'
import SourceManager from '@/components/SourceManager'

export default function SourcesPage() {
  return (
    <div className="container">
      <Navbar active="sources" />
      <div className="header">
        <h1>Knowledge Base</h1>
        <p>Manage your document sources</p>
      </div>
      <div className="main-content">
        <Stats />
        <SourceManager />
      </div>
    </div>
  )
}
