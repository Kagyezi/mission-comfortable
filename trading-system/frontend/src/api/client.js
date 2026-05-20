/**
 * Axios instance pre-configured with the FastAPI base URL.
 * Import this instead of importing axios directly.
 *
 * Usage:
 *   import api from '../api/client'
 *   const data = await api.get('/health')
 */
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// Log errors globally in development
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
