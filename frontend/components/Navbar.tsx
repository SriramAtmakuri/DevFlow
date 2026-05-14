'use client'

import Link from 'next/link'
import { useDispatch, useSelector } from 'react-redux'
import toast from 'react-hot-toast'
import { Brain, MessageSquare, Clock, BarChart2, Folder } from 'lucide-react'
import { logout } from '@/store/slices/authSlice'
import { useLogoutUserMutation } from '@/store/api/devflowApi'
import type { RootState } from '@/store'

interface NavbarProps { active: string }

export default function Navbar({ active }: NavbarProps) {
  const dispatch = useDispatch()
  const { isAuthenticated, username } = useSelector((s: RootState) => s.auth)
  const [logoutUser] = useLogoutUserMutation()

  const handleLogout = async () => {
    try { await logoutUser().unwrap() } catch { /* token revocation is best-effort */ }
    dispatch(logout())
    toast.success('Signed out')
  }

  return (
    <nav className="navbar">
      <Link href="/search" className="navbar-brand">
        <Brain size={24} /> DevFlow
      </Link>
      <div className="navbar-links">
        <Link href="/search" className={`nav-link ${active === 'search' ? 'active' : ''}`}>Search</Link>
        <Link href="/sources" className={`nav-link ${active === 'sources' ? 'active' : ''}`}>Sources</Link>
        <Link href="/chat" className={`nav-link ${active === 'chat' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <MessageSquare size={15} /> Chat
        </Link>
        <Link href="/collections" className={`nav-link ${active === 'collections' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <Folder size={15} /> Collections
        </Link>
        <Link href="/history" className={`nav-link ${active === 'history' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <Clock size={15} /> History
        </Link>
        <Link href="/analytics" className={`nav-link ${active === 'analytics' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <BarChart2 size={15} /> Analytics
        </Link>
        {isAuthenticated ? (
          <>
            <span className="nav-link" style={{ color: '#818cf8' }}>{username}</span>
            <button className="nav-link-btn" onClick={handleLogout}>Sign out</button>
          </>
        ) : (
          <>
            <Link href="/login" className="nav-link">Sign in</Link>
            <Link href="/register" className="nav-link-btn" style={{ textDecoration: 'none' }}>Register</Link>
          </>
        )}
      </div>
    </nav>
  )
}
