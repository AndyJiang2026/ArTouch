/**
 * ArtTouch NFC - NFC Tags API Module
 * @description NFC tag management API calls
 */

import api from './axios'

export const nfcTagsApi = {
  /**
   * Get NFC tags list
   * @param {object} params - { skip, limit, status, approval_status }
   * @returns {Promise<array>}
   */
  list(params = {}) {
    return api.get('/nfc-tags/', { params })
  },

  /**
   * Get NFC tag by ID
   * @param {number} id
   * @returns {Promise<object>}
   */
  get(id) {
    return api.get(`/nfc-tags/${id}`)
  },

  /**
   * Create NFC tag
   * @param {object} data - { url_code, video_id, cultural_product_id }
   * @returns {Promise<object>}
   */
  create(data) {
    return api.post('/nfc-tags/', data)
  },

  /**
   * Update NFC tag
   * @param {number} id
   * @param {object} data
   * @returns {Promise<object>}
   */
  update(id, data) {
    return api.put(`/nfc-tags/${id}`, data)
  },

  /**
   * Delete NFC tag
   * @param {number} id
   * @returns {Promise}
   */
  delete(id) {
    return api.delete(`/nfc-tags/${id}`)
  },

  /**
   * Approve NFC tag
   * @param {number} id
   * @returns {Promise<object>}
   */
  approve(id) {
    return api.post(`/nfc-tags/${id}/approve`)
  },

  /**
   * Reject NFC tag
   * @param {number} id
   * @returns {Promise<object>}
   */
  reject(id) {
    return api.post(`/nfc-tags/${id}/reject`)
  },
}
