/**
 * ArtTouch NFC - Axios API Client
 * @description Main axios instance with interceptors
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor
let isHandlingAuthError = false

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      if (status === 401 && !isHandlingAuthError) {
        isHandlingAuthError = true
        const authStore = useAuthStore()
        authStore.logout()
        router.push({ name: 'Login' })
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error(data.detail || '没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error(data.detail || '资源不存在')
      } else if (status === 422) {
        const messages = Array.isArray(data.detail)
          ? data.detail.map((d) => d.message || d).join(', ')
          : data.detail || '数据验证失败'
        ElMessage.error(messages)
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  },
)

export default api
