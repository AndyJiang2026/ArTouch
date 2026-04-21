/**
 * ArtTouch NFC - Cultural Products API Module
 * @description Cultural product management API calls
 */

import api from './axios'

export const culturalProductsApi = {
  /**
   * Get products list
   * @param {object} params - { skip, limit, status }
   * @returns {Promise<array>}
   */
  list(params = {}) {
    return api.get('/cultural-products/', { params })
  },

  /**
   * Get product by ID
   * @param {number} id
   * @returns {Promise<object>}
   */
  get(id) {
    return api.get(`/cultural-products/${id}`)
  },

  /**
   * Create product
   * @param {object} data - { code, name, description, status }
   * @returns {Promise<object>}
   */
  create(data) {
    return api.post('/cultural-products/', data)
  },

  /**
   * Update product
   * @param {number} id
   * @param {object} data
   * @returns {Promise<object>}
   */
  update(id, data) {
    return api.put(`/cultural-products/${id}`, data)
  },

  /**
   * Delete product
   * @param {number} id
   * @returns {Promise}
   */
  delete(id) {
    return api.delete(`/cultural-products/${id}`)
  },
}
