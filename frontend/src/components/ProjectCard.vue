<script setup>
import { computed } from 'vue';

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
});

const formatNumber = (num) => {
  if (!num) return '0';
  return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
};

const truncate = (text, length) => {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};

// Simple hash for language color since we don't have a full map
const getLangColor = (language) => {
  if (!language) return '#ccc';
  let hash = 0;
  for (let i = 0; i < language.length; i++) {
    hash = language.charCodeAt(i) + ((hash << 5) - hash);
  }
  const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
  return '#' + '00000'.substring(0, 6 - c.length) + c;
};
</script>

<template>
  <div class="project-card">
    <div class="card-header">
      <div class="name-section">
        <a :href="project.url || '#'" target="_blank" class="project-name">{{ project.name }}</a>
        <span class="ai-badge" v-if="project.ai_summary">AI</span>
      </div>
      <div class="stars-badge">
        <span class="star-icon">★</span>
        {{ formatNumber(project.stars) }}
      </div>
    </div>

    <p class="description" :title="project.description">
      {{ truncate(project.description || 'No description provided.', 120) }}
    </p>

    <div class="ai-summary" v-if="project.ai_summary">
      <span class="ai-icon">✨</span> {{ truncate(project.ai_summary, 150) }}
    </div>

    <div class="card-footer">
      <div class="language" v-if="project.language">
        <span class="lang-dot" :style="{ backgroundColor: getLangColor(project.language) }"></span>
        {{ project.language }}
      </div>
      <div class="stars-today" v-if="project.stars_today">
        +{{ formatNumber(project.stars_today) }} today
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-card {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  height: 100%;
  text-align: left;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #646cff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.name-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-name {
  font-weight: 600;
  font-size: 1.1em;
  color: #2c3e50;
  text-decoration: none;
}

.project-name:hover {
  color: #646cff;
}

.ai-badge {
  font-size: 0.7em;
  background: #e0e7ff;
  color: #4f46e5;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.stars-badge {
  display: flex;
  align-items: center;
  font-size: 0.9em;
  color: #666;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 12px;
}

.star-icon {
  color: #e6a23c;
  margin-right: 4px;
}

.description {
  color: #555;
  font-size: 0.95em;
  line-height: 1.5;
  margin: 0 0 12px 0;
  flex-grow: 1;
}

.ai-summary {
  background: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  padding: 8px;
  font-size: 0.85em;
  color: #0c4a6e;
  margin-bottom: 12px;
  border-radius: 0 4px 4px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85em;
  color: #888;
  margin-top: auto;
}

.language {
  display: flex;
  align-items: center;
}

.lang-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
}

.stars-today {
  color: #67c23a;
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .project-card {
    background: #1a1a1a;
    border-color: #333;
  }

  .project-name {
    color: #e0e0e0;
  }

  .description {
    color: #bbb;
  }

  .stars-badge {
    background: #333;
    color: #ccc;
  }

  .ai-summary {
    background: #0c4a6e;
    color: #e0f2fe;
    border-left-color: #38bdf8;
  }
}
</style>
