/**
 * ArtTouch NFC - Videos API Module
 * @description Video management API calls
 */

import api from './axios'

export const videosApi = {
  /**
   * Get videos list
   * @param {object} params - { skip, limit, status }
   * @returns {Promise<array>}
   */
  list(params = {}) {
    return api.get('/videos/', { params })
  },

  /**
   * Get video by ID
   * @param {number} id
   * @returns {Promise<object>}
   */
  get(id) {
    return api.get(`/videos/${id}`)
  },

  /**
   * Upload video
   * @param {FormData} formData
   * @returns {Promise<object>}
   */
  upload(formData) {
    return api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /**
   * Update video
   * @param {number} id
   * @param {object} data
   * @returns {Promise<object>}
   */
  update(id, data) {
    return api.put(`/videos/${id}`, data)
  },

  /**
   * Delete video
   * @param {number} id
   * @returns {Promise}
   */
  delete(id) {
    return api.delete(`/videos/${id}`)
  },
}
