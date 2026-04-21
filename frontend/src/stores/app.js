import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const pageTitle = ref('ArtTouch NFC 互动视频系统')

  function setLoading(value) {
    loading.value = value
  }

  function setPageTitle(title) {
    pageTitle.value = title
  }

  return {
    loading,
    pageTitle,
    setLoading,
    setPageTitle
  }
})
