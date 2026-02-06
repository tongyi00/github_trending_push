import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.DEV ? '' : 'http://localhost:8000',
  timeout: 10000
})

// Request interceptor
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
