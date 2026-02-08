<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
});
</script>

<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3 class="chart-title">{{ title }}</h3>
    </div>

    <div class="chart-content" :class="{ loading: loading }">
      <slot v-if="!loading"></slot>
      <div v-else class="loading-overlay">
        <div class="spinner-wrapper">
          <svg class="spinner" viewBox="0 0 50 50">
            <circle class="spinner-track" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
            <circle class="spinner-head" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
          </svg>
        </div>
        <span class="loading-text">加载图表数据...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}

.chart-container:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: #d1d5db;
}

.chart-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f3f4f6;
}

.chart-title {
  margin: 0;
  font-size: 1.2em;
  font-weight: 600;
  color: #1f2937;
  text-align: left;
}

.chart-content {
  flex-grow: 1;
  position: relative;
  min-height: 240px;
  width: 100%;
  overflow: hidden;
  border-radius: 8px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(248, 250, 252, 0.8);
  backdrop-filter: blur(4px);
  gap: 16px;
  border-radius: 8px;
}

.spinner-wrapper {
  position: relative;
  width: 50px;
  height: 50px;
}

.spinner {
  width: 100%;
  height: 100%;
  animation: rotate 2s linear infinite;
}

.spinner-track {
  stroke: #e5e7eb;
}

.spinner-head {
  stroke: #f59e0b;
  stroke-linecap: round;
  stroke-dasharray: 1, 150;
  stroke-dashoffset: 0;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

.loading-text {
  font-size: 0.95em;
  color: #6b7280;
  font-weight: 500;
}

/* 深色模式 */
:global(.dark) .chart-container {
  background: #1f2937;
  border-color: #374151;
}

:global(.dark) .chart-container:hover {
  border-color: #4b5563;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

:global(.dark) .chart-header {
  border-bottom-color: #374151;
}

:global(.dark) .chart-title {
  color: #f9fafb;
}

:global(.dark) .loading-overlay {
  background: rgba(17, 24, 39, 0.8);
}

:global(.dark) .spinner-track {
  stroke: #374151;
}

:global(.dark) .spinner-head {
  stroke: #fbbf24;
}

:global(.dark) .loading-text {
  color: #9ca3af;
}

/* 移动端优化 */
@media (max-width: 640px) {
  .chart-container {
    padding: 16px;
  }

  .chart-title {
    font-size: 1.1em;
  }

  .chart-content {
    min-height: 200px;
  }
}
</style>
