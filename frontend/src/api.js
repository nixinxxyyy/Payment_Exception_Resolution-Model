/**
 * API client for the Payment Exception Resolution Agent backend.
 *
 * In production (Vercel), set VITE_API_BASE_URL to your Railway/Render backend URL.
 * In local dev, the Vite proxy handles /api → localhost:8000, so BASE stays '/api/v1'.
 */

import axios from 'axios'

// VITE_API_BASE_URL is injected at build time by Vercel env vars.
// Falls back to '/api/v1' for local dev (Vite proxy handles routing).
const BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1'

// Same logic for SSE stream URLs
export const API_ROOT = import.meta.env.VITE_API_BASE_URL || ''

const client = axios.create({
  baseURL: BASE,
  timeout: 120000,   // 2 min — LLM calls can be slow
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor for consistent error handling
client.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg =
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      'Unknown error'
    return Promise.reject(new Error(msg))
  },
)

export const api = {
  /** Submit a new payment exception for resolution */
  submitException:       (data) => client.post('/exceptions/submit', data),

  /** Submit via SSE stream — returns { exception_id, stream_url } */
  submitExceptionStream: (data) => client.post('/exceptions/submit-stream', data),

  /** Get a single exception by ID */
  getException:  (id)    => client.get(`/exceptions/${id}`),

  /** List exceptions with optional filters */
  listExceptions: (params = {}) => client.get('/exceptions', { params }),

  /** Replay / re-evaluate an exception with new status */
  replayException: (id, data) => client.post(`/exceptions/${id}/replay`, data),

  /** Operator override */
  overrideException: (id, data) => client.post(`/exceptions/${id}/override`, data),

  /** System metrics */
  getMetrics: () => client.get('/metrics'),

  /** Health check */
  health: () => axios.get(`${API_ROOT}/health`).then((r) => r.data),

  /** SSE stream URL for a given exception_id */
  streamUrl: (exception_id) => `${API_ROOT}/api/v1/exceptions/${exception_id}/stream`,
}
