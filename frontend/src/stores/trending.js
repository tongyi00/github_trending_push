import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useTrendingStore = defineStore('trending', () => {
  // State
  const projects = ref([])
  const stats = ref({
    totalProjects: 0,
    totalStars: 0,
    languages: []
  })
  const languages = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Actions
  const fetchTrending = async (timeRange = 'daily') => {
    loading.value = true
    error.value = null
    try {
      // Fetch trending projects
      const response = await api.get(`/api/trending/${timeRange}`)
      projects.value = response.data.items

      // Fetch stats
      await fetchStats()

    } catch (err) {
      error.value = err.message || 'Failed to fetch trending data'
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/api/stats/overview')
      const data = response.data

      stats.value = {
        totalProjects: data.total_repositories,
        totalStars: 0, // Not provided by overview API directly, currently
        languages: data.languages || []
      }

      // Update languages list for filter
      languages.value = (data.languages || []).map(l => l.language)

    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  const getProject = (owner, name) => {
    const fullName = `${owner}/${name}`;
    return projects.value.find(p => p.name === fullName);
  }

  return {
    projects,
    stats,
    languages,
    loading,
    error,
    fetchTrending,
    fetchStats,
    getProject
  }
})
