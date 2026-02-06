<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useTrendingStore } from '../stores/trending';
import ProjectCard from '../components/ProjectCard.vue';
import StatCard from '../components/StatCard.vue';
import TimeRangeSelector from '../components/TimeRangeSelector.vue';
import ChartContainer from '../components/ChartContainer.vue';
import LanguageChart from '../components/LanguageChart.vue';

const store = useTrendingStore();
const timeRange = ref('daily');

const fetchData = () => {
  store.fetchTrending(timeRange.value);
  store.fetchStats();
};

const topLanguages = computed(() => {
  return store.stats.languages.slice(0, 8);
});

const topKeywords = computed(() => {
  // Extract keywords from project descriptions
  const keywords = {};
  store.projects.forEach(project => {
    const words = (project.description || '').toLowerCase().split(/\s+/);
    words.forEach(word => {
      if (word.length > 4) {
        keywords[word] = (keywords[word] || 0) + 1;
      }
    });
  });
  return Object.entries(keywords)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([word, count]) => ({ word, count }));
});

onMounted(() => {
  fetchData();
});

watch(timeRange, () => {
  fetchData();
});
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="page-title">GitHub Trending Dashboard</h1>
      <TimeRangeSelector v-model="timeRange" />
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <StatCard
        label="Total Projects"
        :value="store.stats.totalProjects"
        :loading="store.loading"
      />
      <StatCard
        label="Total Stars"
        :value="store.stats.totalStars"
        :loading="store.loading"
        :trend="5.2"
      />
      <StatCard
        label="Top Language"
        :value="store.stats.languages[0]?.name || 'N/A'"
        :loading="store.loading"
      />
    </div>

    <div class="content-grid">
      <!-- Left Column: Project List -->
      <div class="project-list-section">
        <h2 class="section-title">Trending Projects</h2>

        <div v-if="store.loading" class="loading-container">
           <div class="spinner"></div>
        </div>

        <div v-else-if="store.error" class="error-container">
          {{ store.error }}
        </div>

        <div v-else class="project-list">
          <ProjectCard
            v-for="project in store.projects"
            :key="project.name"
            :project="project"
            class="project-item"
          />
        </div>
      </div>

      <!-- Right Column: Charts -->
      <div class="charts-section">
        <div class="chart-wrapper">
          <ChartContainer title="Language Distribution" :loading="store.loading">
            <LanguageChart :data="topLanguages" :loading="store.loading" type="pie" />
          </ChartContainer>
        </div>

        <div class="chart-wrapper">
          <ChartContainer title="Top Keywords" :loading="store.loading">
            <div class="keyword-cloud">
              <span
                v-for="item in topKeywords"
                :key="item.word"
                class="keyword-tag"
                :style="{ fontSize: Math.min(12 + item.count * 2, 24) + 'px' }"
              >
                {{ item.word }}
              </span>
            </div>
          </ChartContainer>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.8em;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.content-grid {
  display: grid;
  grid-template-columns: 3fr 2fr; /* 60% - 40% roughly */
  gap: 24px;
}

.section-title {
  font-size: 1.4em;
  margin-bottom: 16px;
  color: #2c3e50;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.charts-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chart-wrapper {
  height: 350px;
}

.chart-placeholder {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.flex-center {
  align-items: center;
  color: #888;
}

.lang-bar-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-size: 0.9em;
}

.lang-name {
  width: 80px;
  text-align: right;
  margin-right: 10px;
}

.bar-container {
  flex-grow: 1;
  background: #eee;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-right: 10px;
}

.bar {
  height: 100%;
  border-radius: 4px;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #646cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.keyword-cloud {
  padding: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.keyword-tag {
  display: inline-block;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  opacity: 0.85;
}

.keyword-tag:hover {
  opacity: 1;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-color-scheme: dark) {
  .page-title, .section-title {
    color: #e0e0e0;
  }

  .bar-container {
    background: #333;
  }
}
</style>
