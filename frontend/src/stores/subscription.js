import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useSubscriptionStore = defineStore('subscription', () => {
  // State
  const config = ref({
    email_sender: '',
    email_recipients: [],
    keywords: [],
    min_stars: 100,
    scheduler: 'daily',
    ai_models: {
      enabled: [],
      deepseek: {
        api_key: ''
      }
    }
  })

  const loading = ref(false)
  const error = ref(null)

  // Actions
  const fetchConfig = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/api/config/subscription')
      config.value = response.data
    } catch (err) {
      error.value = err.message || 'Failed to fetch config'
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  const updateConfig = async (newConfig) => {
    loading.value = true
    try {
      await api.post('/api/config/subscription', newConfig)
      // Update local state on success
      config.value = { ...config.value, ...newConfig }
      return true
    } catch (err) {
      error.value = err.message || 'Failed to update config'
      console.error(err)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    config,
    loading,
    error,
    fetchConfig,
    updateConfig
  }
})
