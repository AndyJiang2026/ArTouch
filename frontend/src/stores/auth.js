import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api, { refreshApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isFirstLogin = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    // 注意：不要手动设置 Content-Type，axios 会自动为 FormData 添加正确的 boundary
    const response = await api.post('/auth/login', formData)
    
    token.value = response.data.access_token
    refreshToken.value = response.data.refresh_token
    user.value = response.data.user
    isFirstLogin.value = response.data.is_first_login
    
    localStorage.setItem('token', token.value)
    localStorage.setItem('refreshToken', refreshToken.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    
    return response.data
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) return null
    try {
      const formData = new FormData()
      formData.append('refresh_token', refreshToken.value)
      
      // 使用独立的refreshApi实例发送刷新请求（无拦截器），避免401→刷新→401递归
      const response = await refreshApi.post('/auth/refresh-token', formData)
      
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      
      localStorage.setItem('token', token.value)
      localStorage.setItem('refreshToken', refreshToken.value)
      
      if (response.data.user) {
        user.value = response.data.user
        localStorage.setItem('user', JSON.stringify(user.value))
      }
      
      return response.data
    } catch (e) {
      return null
    }
  }

  async function logout() {
    // Clear local state immediately (don't call API with expired token)
    token.value = ''
    refreshToken.value = ''
    user.value = null
    isFirstLogin.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
  }

  async function changePassword(oldPassword, newPassword) {
    const response = await api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    
    if (isFirstLogin.value) {
      isFirstLogin.value = false
    }
    
    return response.data
  }

  async function fetchCurrentUser() {
    if (!token.value) return null
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(user.value))
      return response.data
    } catch (e) {
      logout()
      return null
    }
  }

  return {
    token,
    refreshToken,
    user,
    isFirstLogin,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    refreshAccessToken,
    changePassword,
    fetchCurrentUser
  }
})
