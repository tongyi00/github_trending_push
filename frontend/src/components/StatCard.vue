<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  trend: {
    type: Number,
    default: 0
  },
  loading: {
    type: Boolean,
    default: false
  }
});
</script>

<template>
  <div class="stat-card">
    <div class="stat-content" v-if="!loading">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
      <div class="stat-trend" v-if="trend !== 0" :class="{ up: trend > 0, down: trend < 0 }">
        <span class="trend-arrow">{{ trend > 0 ? '↑' : '↓' }}</span>
        {{ Math.abs(trend) }}%
      </div>
    </div>
    <div class="loading-state" v-else>
      <div class="skeleton-value"></div>
      <div class="skeleton-label"></div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.2s;
}

.stat-card:hover {
  border-color: #646cff;
}

.stat-value {
  font-size: 2.5em;
  font-weight: 700;
  color: var(--text-color, #213547);
  line-height: 1.2;
}

.stat-label {
  font-size: 0.9em;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

.stat-trend {
  margin-top: 8px;
  font-size: 0.9em;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.stat-trend.up {
  color: #67c23a;
}

.stat-trend.down {
  color: #f56c6c;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.skeleton-value {
  width: 60%;
  height: 40px;
  background: #eee;
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

.skeleton-label {
  width: 40%;
  height: 16px;
  background: #eee;
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

@media (prefers-color-scheme: dark) {
  .stat-card {
    background: #1a1a1a;
    border-color: #333;
  }

  .stat-value {
    color: #e0e0e0;
  }

  .skeleton-value, .skeleton-label {
    background: #333;
  }
}
</style>
