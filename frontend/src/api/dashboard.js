/**
 * ArtTouch NFC - Dashboard API Module
 * @description Dashboard statistics API calls
 */

import api from './axios'

export const dashboardApi = {
  /**
   * Get overall statistics
   * @returns {Promise<object>}
   */
  getOverallStats() {
    return api.get('/dashboard/stats')
  },

  /**
   * Get daily statistics
   * @param {string} dateStr - YYYY-MM-DD format
   * @returns {Promise<object>}
   */
  getDailyStats(dateStr) {
    return api.get('/dashboard/daily', { params: { date_str: dateStr } })
  },

  /**
   * Get weekly statistics
   * @param {string} week - YYYY-Www format (e.g., 2026-W16)
   * @returns {Promise<object>}
   */
  getWeeklyStats(week) {
    return api.get('/dashboard/weekly', { params: { week } })
  },

  /**
   * Get monthly statistics
   * @param {string} month - YYYY-MM format (e.g., 2026-04)
   * @returns {Promise<object>}
   */
  getMonthlyStats(month) {
    return api.get('/dashboard/monthly', { params: { month } })
  },
}
