<script setup>
import { ref, onMounted, watch, computed, shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import { useTrendingStore } from '../stores/trending';
import { ElMessage } from 'element-plus';
import ProjectCard from '../components/ProjectCard.vue';
import StatCard from '../components/StatCard.vue';
import TimeRangeSelector from '../components/TimeRangeSelector.vue';
import ChartContainer from '../components/ChartContainer.vue';
import LanguageChart from '../components/LanguageChart.vue';
import { STOP_WORDS, TECH_KEYWORDS } from '../utils/constants';

const store = useTrendingStore();
const router = useRouter();
const timeRange = ref('daily');

const fetchData = () => {
  store.fetchTrending(timeRange.value);
  // fetchStats 已经在 fetchTrending 内部调用，无需重复
};

// 计算总 Stars
const totalStars = computed(() => {
  return store.projects.reduce((sum, p) => sum + (p.stars || 0), 0);
});

// 获取 Top 语言（按百分比最大）
const topLanguage = computed(() => {
  if (store.stats.languages && store.stats.languages.length > 0) {
    // 找到percentage最大的语言
    const maxLang = store.stats.languages.reduce((max, lang) => {
      return (lang.percentage > max.percentage) ? lang : max;
    }, store.stats.languages[0]);
    return maxLang.language;
  }
  return 'N/A';
});

const topLanguages = computed(() => {
  return store.stats.languages.slice(0, 8);
});

const topKeywords = shallowRef([]);

watch(() => store.projects, (projects) => {
  if (!projects || projects.length === 0) {
    topKeywords.value = [];
    return;
  }

  // 使用 requestAnimationFrame 或 setTimeout 将计算推迟到下一次渲染周期，避免阻塞
  setTimeout(() => {
    const keywords = {};
    projects.forEach(project => {
      const text = `${project.name || ''} ${project.description || ''}`.toLowerCase();
      const words = text.match(/[a-z]{3,}/g) || [];
      words.forEach(word => {
        if (!STOP_WORDS.has(word)) {
          const weight = TECH_KEYWORDS.has(word) ? 3 : 1;
          keywords[word] = (keywords[word] || 0) + weight;
        }
      });
    });

    topKeywords.value = Object.entries(keywords)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([word, count]) => ({ word, count }));
  }, 0);
}, { immediate: true });

onMounted(() => {
  fetchData();
});

watch(timeRange, () => {
  fetchData();
});

// 处理查看 AI 分析报告
const handleViewAnalysis = (project) => {
  if (!project.has_ai_analysis) {
    ElMessage.warning({
      message: '暂无 AI 分析报告，该项目还未生成 AI 分析报告。请运行后端的 AI 摘要生成功能。',
      duration: 4000
    });
    return;
  }

  const [owner, name] = project.name.split('/');
  router.push({
    name: 'AnalysisReport',
    params: { owner, name },
    query: {
      description: project.description,
      language: project.language,
      stars: project.stars,
      ai_summary: project.ai_summary
    }
  });
};
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="page-title">Dashboard</h1>
      <TimeRangeSelector v-model="timeRange" />
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <StatCard
        label="Total Projects"
        :value="store.total"
        :loading="store.loading"
      />
      <StatCard
        label="Total Stars"
        :value="totalStars"
        :loading="store.loading"
        :trend="5.2"
      />
      <StatCard
        label="Top Language"
        :value="topLanguage"
        :loading="store.loading"
      />
    </div>

    <div class="content-grid">
      <!-- Left Column: Project List -->
      <div class="project-list-section">
        <h2 class="section-title">项目</h2>

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
            @view-analysis="handleViewAnalysis"
          />
        </div>
      </div>

      <!-- Right Column: Charts -->
      <div class="charts-section">
        <div class="chart-wrapper chart-small">
          <ChartContainer title="语言分布" :loading="store.loading">
            <LanguageChart :data="topLanguages" :loading="store.loading" type="pie" />
          </ChartContainer>
        </div>

        <div class="chart-wrapper chart-large">
          <ChartContainer title="关键词" :loading="store.loading">
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
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 32px 48px;
  overflow: hidden;
  background: transparent; /* 使用 Layout 的背景 */
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  flex-shrink: 0;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: #1D1D1D;
  margin: 0;
  letter-spacing: -0.02em;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
  flex-shrink: 0;
}

.content-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
  flex: 1; /* 占据剩余空间 */
  overflow: hidden; /* 防止网格溢出 */
  min-height: 0; /* 关键：允许Flex子项小于内容高度 */
}

.project-list-section {
  display: flex;
  flex-direction: column;
  height: 100%; /* 填满网格单元格 */
  overflow: hidden;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 20px;
  color: #1D1D1D;
  flex-shrink: 0;
  letter-spacing: -0.01em;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto; /* 左侧独立滚动 */
  padding-right: 8px; /* 给滚动条留点位置 */
  flex: 1;
}

/* 美化滚动条 - Claude 风格 */
.project-list::-webkit-scrollbar,
.charts-section::-webkit-scrollbar,
.keyword-cloud::-webkit-scrollbar {
  width: 6px;
}

.project-list::-webkit-scrollbar-track,
.charts-section::-webkit-scrollbar-track,
.keyword-cloud::-webkit-scrollbar-track {
  background: transparent;
}

.project-list::-webkit-scrollbar-thumb,
.charts-section::-webkit-scrollbar-thumb,
.keyword-cloud::-webkit-scrollbar-thumb {
  background: #E8E6DC;
  border-radius: 3px;
}

.project-list::-webkit-scrollbar-thumb:hover,
.charts-section::-webkit-scrollbar-thumb:hover,
.keyword-cloud::-webkit-scrollbar-thumb:hover {
  background: #B0B0B0;
}

.charts-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%; /* 填满网格单元格 */
  overflow-y: auto; /* 右侧独立滚动 - 解决图表截断问题 */
  padding-right: 8px;
}

.chart-wrapper {
  background: #FFFFFF;
  border: 1px solid #E8E6DC;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s;
}

.chart-wrapper:hover {
  box-shadow: 0 4px 12px rgba(217, 119, 87, 0.08); /* 橙色阴影 */
  border-color: #D97757;
}

.chart-small {
  height: 300px; /* 固定高度，减小空白 */
  min-height: 300px;
  flex-shrink: 0;
}

.chart-large {
  flex: 1; /* 自动占据剩余空间，变大 */
  min-height: 300px;
  overflow: hidden;
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
  color: #6B6B6B;
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
  background: #F3F2EE;
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
  border: 4px solid #E8E6DC;
  border-top: 4px solid #D97757;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.keyword-cloud {
  padding: 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-start;
  align-items: flex-start;
  align-content: flex-start;
  height: 100%;
  overflow-y: auto;
}

.keyword-tag {
  display: inline-block;
  padding: 6px 16px;
  background: #FFF5F0;
  color: #D97757;
  border: 1px solid #FADED2;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  opacity: 0.9;
}

.keyword-tag:hover {
  opacity: 1;
  background: #D97757;
  color: white;
  border-color: #D97757;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(217, 119, 87, 0.2);
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-color-scheme: dark) {
  /* 深色模式适配 */
  :global(.dark) .page-title,
  :global(.dark) .section-title {
    color: #E8E6DC;
  }

  :global(.dark) .chart-wrapper {
    background: #1A1A1A;
    border-color: #2A2A2A;
  }

  :global(.dark) .chart-wrapper:hover {
    box-shadow: 0 4px 12px rgba(232, 139, 111, 0.2);
    border-color: #E88B6F;
  }

  :global(.dark) .bar-container {
    background: #2A2A2A;
  }

  :global(.dark) .project-list::-webkit-scrollbar-thumb,
  :global(.dark) .charts-section::-webkit-scrollbar-thumb,
  :global(.dark) .keyword-cloud::-webkit-scrollbar-thumb {
    background: #4A4A4A;
  }

  :global(.dark) .keyword-tag {
    background: #2A1C18;
    color: #E88B6F;
    border-color: #4A2E26;
  }

  :global(.dark) .keyword-tag:hover {
    background: #E88B6F;
    color: #1A1A1A;
    border-color: #E88B6F;
  }

  :global(.dark) .spinner {
    border-color: #2A2A2A;
    border-top-color: #E88B6F;
  }
}
</style>
