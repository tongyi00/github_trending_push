<template>
  <div class="project-detail">
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>
    <div v-else-if="error" class="error-state">
      <el-result icon="error" title="Error" :sub-title="error">
        <template #extra>
          <el-button type="primary" @click="retryFetch">Retry</el-button>
        </template>
      </el-result>
    </div>
    <div v-else-if="project" class="content">
      <header class="header">
        <div class="nav-back">
          <el-button @click="goBack" link>
            <el-icon class="mr-1"><ArrowLeft /></el-icon> Back to Trending
          </el-button>
        </div>

        <div class="title-section">
          <div class="title-wrapper">
            <h1 class="project-name">
              <span class="owner">{{ owner }}</span>
              <span class="divider">/</span>
              <span class="name">{{ name }}</span>
            </h1>
            <div class="badges">
              <el-tag v-if="project.language" size="small">{{ project.language }}</el-tag>
            </div>
          </div>

          <a :href="`https://github.com/${project.name}`" target="_blank" class="github-link">
            <el-button type="primary" plain>
              View on GitHub <el-icon class="ml-1"><TopRight /></el-icon>
            </el-button>
          </a>
        </div>
      </header>

      <main>
        <section class="summary-section">
          <h2 class="section-title">
            <el-icon><MagicStick /></el-icon> AI Analysis
          </h2>
          <div class="ai-summary card">
            <p>{{ project.summary }}</p>
          </div>
        </section>

        <section class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon"><el-icon><Star /></el-icon></div>
            <div class="stat-info">
              <div class="label">Total Stars</div>
              <div class="value">{{ formatNumber(project.stars) }}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><el-icon><TrendCharts /></el-icon></div>
            <div class="stat-info">
              <div class="label">Stars Today</div>
              <div class="value highlight">+{{ formatNumber(project.todayStars) }}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><el-icon><Connection /></el-icon></div>
            <div class="stat-info">
              <div class="label">Forks</div>
              <div class="value">{{ formatNumber(project.forks || 0) }}</div>
            </div>
          </div>
        </section>

        <section class="description-section">
          <h2 class="section-title">About</h2>
          <div class="description card">
            <p>{{ project.description }}</p>
          </div>
        </section>
      </main>
    </div>
    <div v-else class="not-found">
      <el-empty description="Project not found" />
      <el-button type="primary" @click="goBack">Return Home</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrendingStore } from '@/stores/trending'
import { ArrowLeft, TopRight, MagicStick, Star, TrendCharts, Connection } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useTrendingStore()

const owner = route.params.owner
const name = route.params.name

const project = computed(() => store.getProject(owner, name))
const loading = computed(() => store.loading)
const error = computed(() => store.error)

const goBack = () => {
  router.push('/')
}

const retryFetch = () => {
  store.fetchTrending()
}

const formatNumber = (num) => {
  return new Intl.NumberFormat('en-US').format(num)
}

onMounted(async () => {
  if (!project.value && !store.loading) {
     await store.fetchTrending()
  }
})
</script>

<style scoped>
.project-detail {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.header {
  margin-bottom: 2.5rem;
}

.nav-back {
  margin-bottom: 1.5rem;
}

.title-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}

.project-name {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
}

.owner {
  color: var(--text-secondary);
  font-weight: 400;
}

.divider {
  color: var(--text-tertiary);
}

.badges {
  margin-left: 1rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid var(--border-color);
}

.ai-summary {
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--text-primary);
  background: linear-gradient(to right bottom, #f8faff, #fff);
  border-left: 4px solid var(--primary-color);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin: 2.5rem 0;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.stat-icon {
  background: var(--bg-secondary);
  padding: 0.75rem;
  border-radius: 50%;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.highlight {
  color: #10b981;
}

.description {
  color: var(--text-secondary);
  line-height: 1.6;
}

.mr-1 { margin-right: 0.25rem; }
.ml-1 { margin-left: 0.25rem; }
</style>
