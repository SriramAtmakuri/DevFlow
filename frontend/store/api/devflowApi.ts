import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { RootState } from '../index'
import type { Source, SearchResult, HybridSearchResult, Stats, AuthResponse, JobStatus, SourceChunk } from '../../types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const devflowApi = createApi({
  reducerPath: 'devflowApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_URL}/api`,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token
      if (token) headers.set('authorization', `Bearer ${token}`)
      return headers
    },
  }),
  tagTypes: ['Sources', 'Stats', 'Collections', 'History'],
  endpoints: (builder) => ({
    hybridSearch: builder.mutation<HybridSearchResult, { query: string; use_web?: boolean }>({
      query: (body) => ({ url: '/search/hybrid', method: 'POST', body }),
    }),
    search: builder.mutation<SearchResult, { query: string; n_results?: number }>({
      query: (body) => ({ url: '/search', method: 'POST', body }),
    }),
    getSources: builder.query<{ sources: Source[] }, void>({
      query: () => '/sources',
      providesTags: ['Sources'],
    }),
    getStats: builder.query<Stats, void>({
      query: () => '/stats',
      providesTags: ['Stats'],
    }),
    deleteSource: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({ url: `/sources/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Sources', 'Stats'],
    }),
    addManualDocument: builder.mutation<
      { success: boolean; source_id: number },
      { title: string; content: string; url?: string }
    >({
      query: (body) => ({ url: '/index/manual', method: 'POST', body }),
      invalidatesTags: ['Sources', 'Stats'],
    }),
    saveWebResult: builder.mutation<
      { success: boolean; source_id: number },
      { title: string; url: string; content: string }
    >({
      query: (body) => ({ url: '/save-web-result', method: 'POST', body }),
      invalidatesTags: ['Sources', 'Stats'],
    }),
    login: builder.mutation<AuthResponse, { email: string; password: string }>({
      query: (body) => ({ url: '/auth/login', method: 'POST', body }),
    }),
    register: builder.mutation<AuthResponse, { email: string; password: string; username: string }>({
      query: (body) => ({ url: '/auth/register', method: 'POST', body }),
    }),
    logoutUser: builder.mutation<{ success: boolean }, void>({
      query: () => ({ url: '/auth/logout', method: 'POST' }),
    }),
    getHistory: builder.query<{ history: any[] }, void>({
      query: () => '/history',
      providesTags: ['History'],
    }),
    getAnalytics: builder.query<any, void>({
      query: () => '/analytics',
    }),
    getCollections: builder.query<{ collections: any[] }, void>({
      query: () => '/collections',
      providesTags: ['Collections'],
    }),
    createCollection: builder.mutation<{ success: boolean; collection: any }, { name: string; description?: string }>({
      query: (body) => ({ url: '/collections', method: 'POST', body }),
      invalidatesTags: ['Collections'],
    }),
    deleteCollection: builder.mutation<{ success: boolean }, number>({
      query: (id) => ({ url: `/collections/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Collections'],
    }),
    indexUrl: builder.mutation<{ success: boolean; job_id: string }, { url: string; title?: string; collection_id?: number }>({
      query: (body) => ({ url: '/index/url', method: 'POST', body }),
    }),
    bulkDeleteSources: builder.mutation<{ success: boolean; deleted: number }, { ids: number[] }>({
      query: (body) => ({ url: '/sources/bulk-delete', method: 'POST', body }),
      invalidatesTags: ['Sources', 'Stats'],
    }),
    getSourceChunks: builder.query<{ chunks: SourceChunk[]; total: number }, number>({
      query: (sourceId) => `/sources/${sourceId}/chunks`,
    }),
    getJobStatus: builder.query<JobStatus, string>({
      query: (jobId) => `/upload/status/${jobId}`,
    }),
  }),
})

export const {
  useHybridSearchMutation,
  useSearchMutation,
  useGetSourcesQuery,
  useGetStatsQuery,
  useDeleteSourceMutation,
  useAddManualDocumentMutation,
  useSaveWebResultMutation,
  useLoginMutation,
  useRegisterMutation,
  useLogoutUserMutation,
  useGetHistoryQuery,
  useGetAnalyticsQuery,
  useGetCollectionsQuery,
  useCreateCollectionMutation,
  useDeleteCollectionMutation,
  useIndexUrlMutation,
  useBulkDeleteSourcesMutation,
  useGetSourceChunksQuery,
  useGetJobStatusQuery,
} = devflowApi
