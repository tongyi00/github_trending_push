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
    <div class="header">
      <h3 class="title">{{ title }}</h3>
    </div>

    <div class="chart-content" :class="{ loading: loading }">
      <slot v-if="!loading"></slot>
      <div v-else class="loading-overlay">
        <div class="spinner"></div>
        <span>Loading Chart...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.title {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #2c3e50;
  text-align: left;
}

.chart-content {
  flex-grow: 1;
  position: relative;
  min-height: 300px;
  width: 100%;
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
  background: rgba(255, 255, 255, 0.8);
  gap: 12px;
  color: #888;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #646cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (prefers-color-scheme: dark) {
  .chart-container {
    background: #1a1a1a;
    border-color: #333;
  }

  .header {
    border-bottom-color: #333;
  }

  .title {
    color: #e0e0e0;
  }

  .loading-overlay {
    background: rgba(26, 26, 26, 0.8);
    color: #aaa;
  }

  .spinner {
    border-color: #333;
    border-top-color: #747bff;
  }
}
</style>
