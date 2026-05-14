'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useDispatch } from 'react-redux'
import toast from 'react-hot-toast'
import { useRegisterMutation } from '@/store/api/devflowApi'
import { setCredentials } from '@/store/slices/authSlice'
import Navbar from '@/components/Navbar'

export default function RegisterPage() {
  const router = useRouter()
  const dispatch = useDispatch()
  const [register, { isLoading }] = useRegisterMutation()
  const [form, setForm] = useState({ email: '', username: '', password: '' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = await register(form).unwrap()
      dispatch(setCredentials(data))
      toast.success('Account created!')
      router.push('/search')
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } }
      toast.error(e?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="container">
      <Navbar active="" />
      <div className="auth-card">
        <h2>Create account</h2>
        <p>Start building your knowledge base</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" placeholder="devflow_user" value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })} required minLength={3} />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" placeholder="you@example.com" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" placeholder="Min 8 characters" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ width: '100%', justifyContent: 'center' }}>
            {isLoading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <p style={{ marginTop: 20, textAlign: 'center', color: '#64748b', fontSize: '0.9rem' }}>
          Already have an account? <Link href="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
