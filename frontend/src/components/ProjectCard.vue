<script setup>
import { formatNumber, truncateText, formatDate, getLangColor } from '../utils/formatters';

const props = defineProps({
  project: {
    type: Object,
    required: true,
    validator: (value) => {
      // 基础结构验证，防止传入非项目对象
      return value && typeof value === 'object' && 'name' in value;
    }
  }
});

const emit = defineEmits(['view-analysis']);
</script>

<template>
  <div class="project-card">
    <div class="card-header">
      <div class="name-section">
        <a :href="project.url || '#'" target="_blank" class="project-name">{{ project.name }}</a>
        <span class="ai-badge" v-if="project.ai_summary">
          <svg class="badge-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"/>
          </svg>
          AI
        </span>
      </div>
      <div class="stars-badge">
        <svg class="star-icon" viewBox="0 0 20 20" fill="currentColor">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
        </svg>
        {{ formatNumber(project.stars) }}
      </div>
    </div>

    <p class="description" :title="project.description">
      {{ truncateText(project.description || 'No description provided.', 120) }}
    </p>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-item" v-if="project.stars_increment !== undefined">
        <svg class="stat-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd"/>
        </svg>
        <span class="stat-value">+{{ formatNumber(project.stars_increment) }}</span>
      </div>
      <div class="stat-item" v-if="project.forks !== undefined">
        <svg class="stat-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
        </svg>
        <span class="stat-value">{{ formatNumber(project.forks) }}</span>
      </div>
      <div class="stat-item stat-date" v-if="project.record_date">
        <svg class="stat-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/>
        </svg>
        <span class="stat-value">{{ formatDate(project.record_date) }}</span>
      </div>
    </div>

    <!-- AI Summary Section -->
    <el-popover
      v-if="project.ai_summary"
      placement="right-start"
      :width="400"
      trigger="hover"
      popper-class="ai-summary-popover"
      :show-after="100"
    >
      <template #reference>
        <div class="ai-summary">
          <svg class="ai-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z"/>
          </svg>
          <span class="ai-text">{{ project.ai_summary }}</span>
        </div>
      </template>

      <div class="popover-content">
        <h4 class="popover-title">
          <svg class="ai-icon-small" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z"/>
          </svg>
          AI 分析摘要
        </h4>
        <div class="popover-text">{{ project.ai_summary }}</div>
      </div>
    </el-popover>

    <div class="card-footer">
      <div class="language-tag" v-if="project.language">
        <span class="lang-dot" :style="{ backgroundColor: getLangColor(project.language) }"></span>
        {{ project.language }}
      </div>
      <div class="language-tag" v-else></div>

      <div class="action-buttons">
        <a :href="project.url || '#'" target="_blank" class="btn-action btn-github" title="在 GitHub 上查看">
          <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/>
            <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
          </svg>
        </a>
        <button class="btn-action btn-ai" :class="{ 'btn-disabled': !project.has_ai_analysis }" @click="$emit('view-analysis', project)" :title="project.has_ai_analysis ? '查看 AI 分析' : '暂无 AI 分析'">
          <svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z"/>
          </svg>
          <span class="btn-text">分析</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-card {
  background: #FFFFFF;
  border: 1px solid #E8E6DC;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
  cursor: pointer;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(217, 119, 87, 0.12);
  border-color: #D97757;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
  gap: 12px;
}

.name-section {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.project-name {
  font-weight: 600;
  font-size: 1.1em;
  color: #1D1D1D;
  text-decoration: none;
  word-break: break-word;
  transition: color 0.2s;
}

.project-name:hover {
  color: #D97757;
}

.ai-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75em;
  background: #E8F4EA;
  color: #788C5D;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
  white-space: nowrap;
}

.badge-icon {
  width: 12px;
  height: 12px;
}

.stars-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9em;
  color: #6B6B6B;
  background: #FAF9F5;
  padding: 6px 12px;
  border-radius: 8px;
  white-space: nowrap;
  flex-shrink: 0;
  font-weight: 500;
}

.star-icon {
  width: 16px;
  height: 16px;
  color: #D97757;
}

.description {
  color: #6B6B6B;
  font-size: 0.95em;
  line-height: 1.6;
  margin: 0 0 14px 0;
  flex-grow: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ai-summary {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #FFF8F5;
  border-left: 3px solid #D97757;
  padding: 12px;
  font-size: 0.875em;
  color: #8B4513;
  margin-bottom: 14px;
  border-radius: 0 8px 8px 0;
  line-height: 1.5;
  cursor: help; /* 提示可悬停 */
  transition: all 0.2s ease;
}

.ai-summary:hover {
  background: #FFF0EB;
}

.ai-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  margin-top: 2px;
  color: #D97757;
}

.ai-text {
  flex: 1;
  /* 始终保持2行截断 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 移除之前的悬停自动展开逻辑 */
/*.ai-summary:hover .ai-text {
  -webkit-line-clamp: unset;
}*/

.stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 0;
  margin-bottom: 14px;
  border-top: 1px solid #F3F2EE;
  border-bottom: 1px solid #F3F2EE;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875em;
  color: #6B6B6B;
  transition: all 0.2s ease;
  cursor: default;
}

.stat-item:hover {
  color: #1D1D1D;
}

.stat-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.stat-value {
  font-weight: 500;
}

.stat-date {
  margin-left: auto;
  color: #B0AEA5;
  font-size: 0.85em;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875em;
  color: #6B6B6B;
  margin-top: auto;
  gap: 12px;
  min-height: 36px;
}

.language-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.lang-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.9em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  border: none;
  font-family: inherit;
}

.btn-github {
  background: #F7F6F2;
  color: #6B6B6B;
  border: 1px solid #E8E6DC;
}

.btn-github:hover {
  background: #F3F2EE;
  color: #1D1D1D;
  border-color: #D1CFC4;
  transform: translateY(-1px);
}

.btn-ai {
  background: #1D1D1D;
  color: #FFFFFF;
  border: 1px solid transparent;
}

.btn-ai:hover {
  background: #D97757;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(217, 119, 87, 0.3);
}

.btn-disabled {
  background: #F3F2EE;
  color: #B0AEA5;
  cursor: not-allowed;
  opacity: 0.6;
  border: 1px solid #E8E6DC;
}

.btn-disabled:hover {
  background: #F3F2EE;
  transform: none;
  box-shadow: none;
}

.btn-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.btn-text {
  font-size: 0.95em;
}

/* 深色模式 - Claude Aesthetic Dark */
:global(.dark) .project-card {
  background: #1A1A1A;
  border-color: #2A2A2A;
}

:global(.dark) .project-card:hover {
  border-color: #E88B6F;
  box-shadow: 0 12px 24px rgba(232, 139, 111, 0.2);
}

:global(.dark) .project-name {
  color: #E8E6DC;
}

:global(.dark) .project-name:hover {
  color: #E88B6F;
}

:global(.dark) .ai-badge {
  background: #2A3428;
  color: #98AA85;
}

:global(.dark) .stars-badge {
  background: #0F0F0F;
  color: #B0AEA5;
}

:global(.dark) .description {
  color: #B0AEA5;
}

:global(.dark) .ai-summary {
  background: #2A1C18;
  color: #E8C4B0;
  border-left-color: #E88B6F;
}

:global(.dark) .stats-bar {
  border-top-color: #2A2A2A;
  border-bottom-color: #2A2A2A;
}

:global(.dark) .stat-item {
  color: #B0AEA5;
}

:global(.dark) .stat-item:hover {
  color: #E8E6DC;
}

:global(.dark) .stat-date {
  color: #7A7870;
}

:global(.dark) .language-tag {
  color: #B0AEA5;
}

:global(.dark) .btn-github {
  background: #0F0F0F;
  color: #B0AEA5;
  border-color: #2A2A2A;
}

:global(.dark) .btn-github:hover {
  background: #1A1A1A;
  color: #E8E6DC;
  border-color: #3A3A3A;
}

:global(.dark) .btn-ai {
  background: #E8E6DC;
  color: #1D1D1D;
}

:global(.dark) .btn-ai:hover {
  background: #E88B6F;
  color: #FFFFFF;
}

:global(.dark) .btn-disabled {
  background: #1A1A1A;
  color: #4A4A4A;
  border-color: #2A2A2A;
}

/* 移动端优化 */
@media (max-width: 640px) {
  .project-card {
    padding: 16px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .stars-badge {
    align-self: flex-start;
  }

  .stats-bar {
    gap: 12px;
  }

  .stat-date {
    width: 100%;
    margin-left: 0;
  }

  .action-buttons {
    width: 100%;
  }

  .btn-action {
    flex: 1;
    justify-content: center;
  }
}
</style>

<style>
/* 全局 Popover 样式 - 必须是非 scoped 才能作用于 body 下的 popover */
.ai-summary-popover {
  padding: 16px !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  border: 1px solid #E8E6DC !important;
  max-width: 400px !important;
}

.popover-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #D97757;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #F3F2EE;
}

.ai-icon-small {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: block;
  color: #D97757;
}

.popover-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #1D1D1D;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

/* 深色模式适配 */
.dark .ai-summary-popover {
  background: #2A1C18 !important;
  border-color: #4A2E26 !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
}

.dark .popover-title {
  color: #E88B6F;
  border-bottom-color: #4A2E26;
}

.dark .popover-text {
  color: #E8C4B0;
}
</style>
