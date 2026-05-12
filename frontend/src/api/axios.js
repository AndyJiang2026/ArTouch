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
  // Note: Do NOT set default Content-Type here. 
  // Axios auto-detects: JSON objects → application/json, FormData → multipart/form-data
  // Explicit Content-Type breaks FormData (axios treats it as JSON and JSON.stringifies it)
})

// Separate axios instance for refresh token (avoids interceptor loop)
const refreshApi = axios.create({
  baseURL: '/api',
  timeout: 30000,
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
let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach((callback) => callback(newToken))
  refreshSubscribers = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response) {
      const { status, data } = error.response

      // Handle 401 - try refresh token first
      if (status === 401 && !originalRequest._retry) {
        if (isRefreshing) {
          // Already refreshing, queue this request
          return new Promise((resolve) => {
            subscribeTokenRefresh((newToken) => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              resolve(api(originalRequest))
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        const authStore = useAuthStore()
        // 使用独立的refreshApi实例发送刷新请求，避免递归进入当前拦截器
        const result = await authStore.refreshAccessToken()

        if (result) {
          // Refresh succeeded, update header and retry
          isRefreshing = false
          onTokenRefreshed(result.access_token)
          originalRequest.headers.Authorization = `Bearer ${result.access_token}`
          return api(originalRequest)
        } else {
          // Refresh failed, logout and redirect
          isRefreshing = false
          authStore.logout()
          // Only redirect and show error if not already on login page
          if (router.currentRoute.value.name !== 'Login') {
            router.push({ name: 'Login' })
            ElMessage.error('登录已过期，请重新登录')
          }
          return Promise.reject(error)
        }
      }

      if (status === 401 && originalRequest._retry) {
        // Refresh already tried and failed
        const authStore = useAuthStore()
        authStore.logout()
        // Only redirect and show error if not already on login page
        if (router.currentRoute.value.name !== 'Login') {
          router.push({ name: 'Login' })
          ElMessage.error('登录已过期，请重新登录')
        }
        return Promise.reject(error)
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
export { refreshApi }
