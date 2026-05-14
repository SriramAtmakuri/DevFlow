'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useDispatch } from 'react-redux'
import toast from 'react-hot-toast'
import { useLoginMutation } from '@/store/api/devflowApi'
import { setCredentials } from '@/store/slices/authSlice'
import Navbar from '@/components/Navbar'

export default function LoginPage() {
  const router = useRouter()
  const dispatch = useDispatch()
  const [login, { isLoading }] = useLoginMutation()
  const [form, setForm] = useState({ email: '', password: '' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = await login(form).unwrap()
      dispatch(setCredentials(data))
      toast.success(`Welcome back, ${data.username}!`)
      router.push('/search')
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } }
      toast.error(e?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="container">
      <Navbar active="" />
      <div className="auth-card">
        <h2>Welcome back</h2>
        <p>Sign in to your DevFlow account</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" placeholder="you@example.com" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" placeholder="••••••••" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ width: '100%', justifyContent: 'center' }}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p style={{ marginTop: 20, textAlign: 'center', color: '#64748b', fontSize: '0.9rem' }}>
          No account? <Link href="/register" className="auth-link">Create one</Link>
        </p>
      </div>
    </div>
  )
}
