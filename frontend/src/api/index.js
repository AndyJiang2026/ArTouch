/**
 * ArtTouch NFC - API Modules Index
 * @description Re-exports all API modules for convenient imports
 *
 * Usage:
 *   import api, { authApi, videosApi } from '@/api'
 *   // or
 *   import { dashboardApi } from '@/api'
 */

import axios from './axios'
export default axios
export { authApi } from './auth'
export { videosApi } from './videos'
export { culturalProductsApi } from './culturalProducts'
export { nfcTagsApi } from './nfcTags'
export { dashboardApi } from './dashboard'
