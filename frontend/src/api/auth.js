/**
 * ArtTouch NFC - Auth API Module
 * @description Authentication and user management API calls
 */

import api from './axios'

export const authApi = {
  /**
   * User login
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{access_token: string, user: object}>}
   */
  login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    // 注意：不要手动设置 Content-Type，axios 会自动为 FormData 添加正确的 boundary
    return api.post('/auth/login', formData)
  },

  /**
   * User logout
   * @returns {Promise}
   */
  logout() {
    return api.post('/auth/logout')
  },

  /**
   * Get current user info
   * @returns {Promise<object>}
   */
  getCurrentUser() {
    return api.get('/auth/me')
  },

  /**
   * Change password
   * @param {string} oldPassword
   * @param {string} newPassword
   * @returns {Promise}
   */
  changePassword(oldPassword, newPassword) {
    return api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  },
}
