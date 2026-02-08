import axios from 'axios'
import { getAuthToken, clearAuthToken } from '@/utils/auth'
import { ElMessage } from 'element-plus'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

if (import.meta.env.PROD && !baseURL) {
  console.warn('VITE_API_BASE_URL is not set. API requests will be relative to current origin.')
}

const api = axios.create({
  baseURL,
  timeout: 30000
})

// Request interceptor - 统一添加认证头
api.interceptors.request.use(
  config => {
    const token = getAuthToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 错误码映射
const ERROR_MESSAGES = {
  400: '请求参数错误',
  401: '认证已过期，请重新登录',
  403: '拒绝访问：没有权限',
  404: '请求的资源未找到',
  405: '请求方法不允许',
  408: '请求超时',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  501: '服务未实现',
  502: '网关错误',
  503: '服务不可用',
  504: '网关超时',
  'ECONNABORTED': '请求超时，请检查网络',
  'NETWORK_ERROR': '网络连接失败，请检查您的网络设置'
}

// Response interceptor
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 处理 API 错误
    const status = error.response ? error.response.status : null

    if (status === 401) {
      console.error('Unauthorized: Invalid or expired token')
      clearAuthToken()
      if (window.location.pathname !== '/login') {
         window.location.href = '/login'
         ElMessage.error(ERROR_MESSAGES[401])
      }
      return Promise.reject(error)
    }

    const message = ERROR_MESSAGES[status] || ERROR_MESSAGES[error.code] || (error.response ? `请求失败 (${status})` : ERROR_MESSAGES['NETWORK_ERROR'])

    ElMessage.error(message)

    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
