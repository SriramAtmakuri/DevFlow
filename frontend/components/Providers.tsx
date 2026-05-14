'use client'

import { useEffect } from 'react'
import { Provider, useDispatch } from 'react-redux'
import { Toaster } from 'react-hot-toast'
import { store, AppDispatch } from '@/store'
import { restoreAuth } from '@/store/slices/authSlice'

function AuthRestorer({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch<AppDispatch>()
  useEffect(() => { dispatch(restoreAuth()) }, [dispatch])
  return <>{children}</>
}

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <AuthRestorer>{children}</AuthRestorer>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { background: '#1e293b', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.1)' },
          success: { iconTheme: { primary: '#34d399', secondary: '#1e293b' } },
          error: { iconTheme: { primary: '#f87171', secondary: '#1e293b' } },
        }}
      />
    </Provider>
  )
}
