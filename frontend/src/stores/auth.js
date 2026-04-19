import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isFirstLogin = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    token.value = response.data.access_token
    user.value = response.data.user
    isFirstLogin.value = response.data.is_first_login
    
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    
    return response.data
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (e) {
      // Ignore logout errors
    }
    token.value = ''
    user.value = null
    isFirstLogin.value = false
    localStorage.removeItem('token')
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
    user,
    isFirstLogin,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    changePassword,
    fetchCurrentUser
  }
})
