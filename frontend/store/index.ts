import { configureStore } from '@reduxjs/toolkit'
import { devflowApi } from './api/devflowApi'
import authReducer from './slices/authSlice'

export const store = configureStore({
  reducer: {
    [devflowApi.reducerPath]: devflowApi.reducer,
    auth: authReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(devflowApi.middleware),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
