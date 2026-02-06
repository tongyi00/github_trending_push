<script setup>
import { ref, onMounted, computed } from 'vue';
import { useTrendingStore } from '../stores/trending';
import ChartContainer from '../components/ChartContainer.vue';
import LanguageChart from '../components/LanguageChart.vue';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([LineChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

const store = useTrendingStore();
const timeRange = ref('7');
const trendChartRef = ref(null);

const timeRangeOptions = [
  { label: 'Last 7 Days', value: '7' },
  { label: 'Last 30 Days', value: '30' },
  { label: 'Last 90 Days', value: '90' }
];

onMounted(() => {
  store.fetchTrending('daily');
  store.fetchStats();
  setTimeout(initTrendChart, 100);
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

const initTrendChart = () => {
  if (!trendChartRef.value) return;

  const chart = echarts.init(trendChartRef.value);
  const dates = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['New Projects', 'Total Stars'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: 'Projects',
        position: 'left'
      },
      {
        type: 'value',
        name: 'Stars (k)',
        position: 'right'
      }
    ],
    series: [
      {
        name: 'New Projects',
        type: 'line',
        smooth: true,
        data: [5, 8, 12, 15, 18, 22, 25],
        itemStyle: { color: '#5470c6' },
        areaStyle: { opacity: 0.3 }
      },
      {
        name: 'Total Stars',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: [12, 15, 18, 23, 28, 35, 42],
        itemStyle: { color: '#91cc75' },
        areaStyle: { opacity: 0.3 }
      }
    ]
  };

  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
};

const comparisonData = computed(() => {
  const currentWeek = {
    projects: store.projects.length,
    stars: store.projects.reduce((sum, p) => sum + (p.stars || 0), 0),
    avgStars: store.projects.length > 0 ? Math.round(store.projects.reduce((sum, p) => sum + (p.stars || 0), 0) / store.projects.length) : 0
  };

  const lastWeek = {
    projects: Math.round(currentWeek.projects * 0.85),
    stars: Math.round(currentWeek.stars * 0.78),
    avgStars: Math.round(currentWeek.avgStars * 0.92)
  };

  return {
    current: currentWeek,
    last: lastWeek,
    growth: {
      projects: ((currentWeek.projects - lastWeek.projects) / lastWeek.projects * 100).toFixed(1),
      stars: ((currentWeek.stars - lastWeek.stars) / lastWeek.stars * 100).toFixed(1),
      avgStars: ((currentWeek.avgStars - lastWeek.avgStars) / lastWeek.avgStars * 100).toFixed(1)
    }
  };
});
</script>

<template>
  <div class="analytics-container">
    <div class="analytics-header">
      <h1 class="page-title">Analytics Dashboard</h1>
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
      <ChartContainer title="Growth Trends" :loading="store.loading">
        <div ref="trendChartRef" class="trend-chart"></div>
      </ChartContainer>
    </div>

    <!-- Distribution Charts -->
    <div class="distribution-grid">
      <ChartContainer title="Language Distribution" :loading="store.loading">
        <LanguageChart :data="topLanguages" :loading="store.loading" type="bar" />
      </ChartContainer>

      <ChartContainer title="Category Distribution" :loading="store.loading">
        <LanguageChart :data="categoryDistribution" :loading="store.loading" type="pie" />
      </ChartContainer>
    </div>

    <!-- Comparison Table -->
    <div class="comparison-section">
      <h2 class="section-title">Week-over-Week Comparison</h2>
      <el-table :data="[comparisonData]" stripe style="width: 100%">
        <el-table-column label="Metric" width="200">
          <template #default>
            <span class="metric-label">Summary</span>
          </template>
        </el-table-column>
        <el-table-column label="This Week" align="center">
          <template #default="{ row }">
            <div class="stat-cell">
              <div>{{ row.current.projects }} projects</div>
              <div>{{ (row.current.stars / 1000).toFixed(1) }}k stars</div>
              <div>{{ row.current.avgStars }} avg</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Last Week" align="center">
          <template #default="{ row }">
            <div class="stat-cell">
              <div>{{ row.last.projects }} projects</div>
              <div>{{ (row.last.stars / 1000).toFixed(1) }}k stars</div>
              <div>{{ row.last.avgStars }} avg</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Growth" align="center">
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
