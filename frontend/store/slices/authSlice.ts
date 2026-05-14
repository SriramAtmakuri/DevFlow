import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AuthState {
  token: string | null
  user_id: number | null
  username: string | null
  isAuthenticated: boolean
}

const initialState: AuthState = {
  token: null,
  user_id: null,
  username: null,
  isAuthenticated: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials(state, action: PayloadAction<{ access_token: string; user_id: number; username: string }>) {
      state.token = action.payload.access_token
      state.user_id = action.payload.user_id
      state.username = action.payload.username
      state.isAuthenticated = true
      if (typeof window !== 'undefined') {
        localStorage.setItem('devflow_token', action.payload.access_token)
        localStorage.setItem('devflow_user', JSON.stringify({ user_id: action.payload.user_id, username: action.payload.username }))
      }
    },
    logout(state) {
      state.token = null
      state.user_id = null
      state.username = null
      state.isAuthenticated = false
      if (typeof window !== 'undefined') {
        localStorage.removeItem('devflow_token')
        localStorage.removeItem('devflow_user')
      }
    },
    restoreAuth(state) {
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('devflow_token')
        const userStr = localStorage.getItem('devflow_user')
        if (token && userStr) {
          const user = JSON.parse(userStr)
          state.token = token
          state.user_id = user.user_id
          state.username = user.username
          state.isAuthenticated = true
        }
      }
    },
  },
})

export const { setCredentials, logout, restoreAuth } = authSlice.actions
export default authSlice.reducer
