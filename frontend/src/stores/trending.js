import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

const CACHE_TTL = 5 * 60 * 1000  // 5 minutes

export const useTrendingStore = defineStore('trending', () => {
  // State
  const projects = ref([])
  const total = ref(0) // 新增：保存当前列表总数
  const stats = ref({
    totalProjects: 0,
    totalStars: 0,
    languages: []
  })
  const languages = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const projectsMap = computed(() => {
    const map = new Map()
    projects.value.forEach(p => {
      if (p.name) {
        map.set(p.name, p)
      }
    })
    return map
  })

  // Cache state
  const lastFetchTime = ref(null)
  const lastTimeRange = ref(null)
  const statsFetched = ref(false)

  const isCacheValid = (timeRange) => {
    if (!lastFetchTime.value || lastTimeRange.value !== timeRange) return false
    return Date.now() - lastFetchTime.value < CACHE_TTL
  }

  // Actions
  const fetchTrending = async (timeRange = 'daily', forceRefresh = false) => {
    if (!forceRefresh && isCacheValid(timeRange) && projects.value.length > 0) {
      return
    }

    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/api/trending/${timeRange}`)

      // 数据结构验证
      if (!response.data || !Array.isArray(response.data.items)) {
        throw new Error('Invalid response data format: items array expected')
      }

      projects.value = response.data.items
      total.value = response.data.total || response.data.items.length // 更新总数
      lastFetchTime.value = Date.now()
      lastTimeRange.value = timeRange

      if (!statsFetched.value || forceRefresh) {
        await fetchStats()
      }
    } catch (err) {
      error.value = err.message || 'Failed to fetch trending data'
      console.error(err)
      // 如果数据格式错误，清空列表以避免渲染问题
      projects.value = []
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async (forceRefresh = false) => {
    if (!forceRefresh && statsFetched.value) return

    try {
      // 并行获取 overview 和 languages 数据
      const [overviewRes, languagesRes] = await Promise.all([
        api.get('/api/stats/overview'),
        api.get('/api/stats/languages')
      ])

      const overviewData = overviewRes.data
      const languagesData = languagesRes.data

      if (!overviewData) throw new Error('Invalid stats data')

      stats.value = {
        totalProjects: overviewData.total_repositories || 0,
        totalStars: 0,
        languages: Array.isArray(languagesData) ? languagesData : []
      }
      languages.value = (languagesData || []).map(l => l.language)
      statsFetched.value = true
    } catch (err) {
      console.error('Failed to fetch stats:', err)
      // 设置默认空状态
      stats.value = { totalProjects: 0, totalStars: 0, languages: [] }
    }
  }

  const getProject = (owner, name) => {
    const fullName = `${owner}/${name}`;
    return projectsMap.value.get(fullName);
  }

  return {
    projects,
    total, // 导出 total
    stats,
    languages,
    loading,
    error,
    fetchTrending,
    fetchStats,
    getProject
  }
})
