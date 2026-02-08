<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useTrendingStore } from '../stores/trending';
import ChartContainer from '../components/ChartContainer.vue';
import LanguageChart from '../components/LanguageChart.vue';
import api from '../api';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { useChart } from '../composables/useChart';

echarts.use([LineChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

const store = useTrendingStore();
const timeRange = ref('7');
const trendChartRef = ref(null);
const historyData = ref([]);
const comparisonData = ref(null);
const historyLoading = ref(false);
const comparisonLoading = ref(false);

const timeRangeOptions = [
  { label: 'Last 7 Days', value: '7' },
  { label: 'Last 30 Days', value: '30' },
  { label: 'Last 90 Days', value: '90' }
];

const fetchHistoryStats = async (days) => {
  historyLoading.value = true;
  try {
    const response = await api.get(`/api/stats/history?days=${days}`);
    historyData.value = response.data.data || [];
  } catch (error) {
    console.error('Failed to fetch history stats:', error);
    historyData.value = [];
  } finally {
    historyLoading.value = false;
  }
};

const fetchComparison = async () => {
  comparisonLoading.value = true;
  try {
    const response = await api.get('/api/stats/comparison');
    comparisonData.value = response.data;
  } catch (error) {
    console.error('Failed to fetch comparison:', error);
    comparisonData.value = null;
  } finally {
    comparisonLoading.value = false;
  }
};

onMounted(() => {
  store.fetchTrending('daily');
  fetchHistoryStats(parseInt(timeRange.value));
  fetchComparison();
});

watch(timeRange, (newVal) => {
  fetchHistoryStats(parseInt(newVal));
});

const topLanguages = computed(() => store.stats.languages.slice(0, 10));

const categoryDistribution = computed(() => {
  const categories = {
    'Web Development': 0,
    'Machine Learning': 0,
    'DevOps': 0,
    'Mobile': 0,
    'Data Science': 0,
    'Other': 0
  };

  store.projects.forEach(project => {
    const desc = (project.description || '').toLowerCase();
    if (desc.includes('web') || desc.includes('frontend') || desc.includes('backend')) {
      categories['Web Development']++;
    } else if (desc.includes('ml') || desc.includes('ai') || desc.includes('neural')) {
      categories['Machine Learning']++;
    } else if (desc.includes('docker') || desc.includes('kubernetes') || desc.includes('ci/cd')) {
      categories['DevOps']++;
    } else if (desc.includes('mobile') || desc.includes('android') || desc.includes('ios')) {
      categories['Mobile']++;
    } else if (desc.includes('data') || desc.includes('analytics')) {
      categories['Data Science']++;
    } else {
      categories['Other']++;
    }
  });

  return Object.entries(categories).map(([name, count]) => ({
    name,
    count,
    percentage: store.projects.length > 0 ? ((count / store.projects.length) * 100).toFixed(1) : 0
  })).filter(item => item.count > 0);
});

const hasHistoryData = computed(() => historyData.value.some(d => d.project_count > 0 || d.total_stars > 0));

const trendChartOption = computed(() => {
  if (!historyData.value.length) return null;

  const dates = historyData.value.map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  const projectCounts = historyData.value.map(d => d.project_count);
  const starCounts = historyData.value.map(d => Math.round(d.total_stars / 1000));

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['New Projects', 'Total Stars (k)'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '10%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: [
      { type: 'value', name: 'Projects', position: 'left' },
      { type: 'value', name: 'Stars (k)', position: 'right' }
    ],
    series: [
      { name: 'New Projects', type: 'line', smooth: true, data: projectCounts, itemStyle: { color: '#5470c6' }, areaStyle: { opacity: 0.3 } },
      { name: 'Total Stars (k)', type: 'line', smooth: true, yAxisIndex: 1, data: starCounts, itemStyle: { color: '#91cc75' }, areaStyle: { opacity: 0.3 } }
    ]
  };
});

useChart(trendChartRef, trendChartOption);

</script>

<template>
  <div class="analytics-container">
    <div class="analytics-header">
      <h1 class="page-title">趋势分析 Dashboard</h1>
      <el-select v-model="timeRange" class="time-selector">
        <el-option
          v-for="option in timeRangeOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
    </div>

    <!-- Trend Chart -->
    <div class="chart-section">
      <ChartContainer title="增长趋势" :loading="historyLoading">
        <div v-if="hasHistoryData" ref="trendChartRef" class="trend-chart"></div>
        <div v-else class="no-data-placeholder">
          <el-empty description="No historical data available. Data will appear after collecting trends for multiple days." />
        </div>
      </ChartContainer>
    </div>

    <!-- Distribution Charts -->
    <div class="distribution-grid">
      <ChartContainer title="语言分布" :loading="store.loading">
        <LanguageChart :data="topLanguages" :loading="store.loading" type="bar" />
      </ChartContainer>

      <ChartContainer title="类别分布" :loading="store.loading">
        <LanguageChart :data="categoryDistribution" :loading="store.loading" type="pie" />
      </ChartContainer>
    </div>

    <!-- Comparison Table -->
    <div class="comparison-section">
      <h2 class="section-title">周对比</h2>
      <div v-if="comparisonLoading" class="loading-placeholder">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="comparisonData && (comparisonData.current.projects > 0 || comparisonData.last.projects > 0)">
        <el-table :data="[comparisonData]" stripe style="width: 100%">
          <el-table-column label="指标" width="200">
            <template #default>
              <span class="metric-label">Summary</span>
            </template>
          </el-table-column>
          <el-table-column label="当周" align="center">
            <template #default="{ row }">
              <div class="stat-cell">
                <div>{{ row.current.projects }} projects</div>
                <div>{{ (row.current.stars / 1000).toFixed(1) }}k stars</div>
                <div>{{ row.current.avg_stars }} avg</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="上周" align="center">
            <template #default="{ row }">
              <div class="stat-cell">
                <div>{{ row.last.projects }} projects</div>
                <div>{{ (row.last.stars / 1000).toFixed(1) }}k stars</div>
                <div>{{ row.last.avg_stars }} avg</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="趋势" align="center">
            <template #default="{ row }">
              <div class="growth-cell">
                <el-tag :type="row.growth.projects > 0 ? 'success' : 'danger'" size="small">
                  {{ row.growth.projects > 0 ? '+' : '' }}{{ row.growth.projects }}%
                </el-tag>
                <el-tag :type="row.growth.stars > 0 ? 'success' : 'danger'" size="small">
                  {{ row.growth.stars > 0 ? '+' : '' }}{{ row.growth.stars }}%
                </el-tag>
                <el-tag :type="row.growth.avgStars > 0 ? 'success' : 'danger'" size="small">
                  {{ row.growth.avgStars > 0 ? '+' : '' }}{{ row.growth.avgStars }}%
                </el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else class="no-data-placeholder">
        <el-empty description="No comparison data available. Need at least 2 weeks of data for comparison." />
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}

.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 1.8em;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.time-selector {
  width: 200px;
}

.chart-section {
  margin-bottom: 32px;
}

.trend-chart {
  width: 100%;
  height: 400px;
}

.distribution-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.comparison-section {
  margin-top: 32px;
}

.section-title {
  font-size: 1.4em;
  margin-bottom: 16px;
  color: #2c3e50;
}

.metric-label {
  font-weight: 600;
  color: #2c3e50;
}

.stat-cell, .growth-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.growth-cell {
  align-items: center;
}

@media (prefers-color-scheme: dark) {
  .page-title, .section-title, .metric-label {
    color: #e0e0e0;
  }
}
</style>
