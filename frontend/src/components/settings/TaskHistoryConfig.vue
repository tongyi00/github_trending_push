<script setup>
import { ref } from 'vue'

const props = defineProps({
  taskHistory: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['run'])

const selectedTaskType = ref('daily')
const runningTask = ref(null)

const handleRunTask = async () => {
  runningTask.value = selectedTaskType.value
  emit('run', selectedTaskType.value, () => {
    runningTask.value = null
  })
}

const formatDateTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const getStatusType = (status) => {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  return 'warning'
}

const getStatusIcon = (status) => {
  if (status === 'success') return '✓'
  if (status === 'failed') return '✗'
  return '⋯'
}
</script>

<template>
  <el-card class="settings-card">
    <template #header>
      <span class="card-title">任务执行</span>
    </template>

    <div class="manual-run">
      <span class="section-label">手动执行</span>
      <div class="run-controls">
        <el-select v-model="selectedTaskType" size="small" style="width: 120px">
          <el-option label="日榜" value="daily" />
          <el-option label="周榜" value="weekly" />
          <el-option label="月榜" value="monthly" />
        </el-select>
        <el-button type="primary" size="small" @click="handleRunTask" :loading="runningTask !== null" class="btn-primary-custom">执行</el-button>
      </div>
    </div>

    <el-divider />

    <div class="task-history">
      <span class="section-label">最近执行记录</span>
      <div class="history-list" v-if="taskHistory.length > 0">
        <div class="history-item" v-for="item in taskHistory" :key="item.id">
          <span class="history-time">{{ formatDateTime(item.started_at) }}</span>
          <span class="history-type">{{ item.task_type }}</span>
          <el-tag :type="getStatusType(item.status)" size="small" effect="light">{{ getStatusIcon(item.status) }} {{ item.status }}</el-tag>
          <span class="history-error" v-if="item.error_message">{{ item.error_message }}</span>
        </div>
      </div>
      <div class="no-history" v-else>
        <el-empty description="暂无执行记录" :image-size="60" />
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.settings-card {
  border-radius: 12px;
  margin-bottom: 24px;
  border: 1px solid #E8E6DC;
  background: #FFFFFF;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.settings-card :deep(.el-card__header) {
  border-bottom: 1px solid #E8E6DC;
  padding: 16px 20px;
}

.card-title { font-weight: 600; font-size: 16px; color: #1D1D1D; }

.section-label { font-weight: 600; display: block; margin-bottom: 16px; color: #1D1D1D; }
.manual-run .run-controls { display: flex; gap: 12px; align-items: center; }

.task-history .history-list { display: flex; flex-direction: column; gap: 8px; }
.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #F7F6F2;
  border-radius: 8px;
  font-size: 13px;
  color: #1D1D1D;
}
.history-time { color: #6B6B6B; min-width: 120px; font-family: 'IBM Plex Mono', monospace; }
.history-type { font-weight: 600; min-width: 80px; text-transform: capitalize; }
.history-error { color: #D97757; font-size: 12px; margin-left: auto; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.no-history { padding: 30px; }

.btn-primary-custom {
  background-color: #1D1D1D;
  border-color: #1D1D1D;
  color: #FFFFFF;
  font-weight: 500;
}
.btn-primary-custom:hover, .btn-primary-custom:focus {
  background-color: #D97757;
  border-color: #D97757;
  color: #FFFFFF;
}

/* Dark mode */
:global(.dark) .settings-card {
  background: #1A1A1A;
  border-color: #2A2A2A;
}
:global(.dark) .settings-card :deep(.el-card__header) {
  border-bottom-color: #2A2A2A;
}
:global(.dark) .card-title { color: #E8E6DC; }
:global(.dark) .section-label { color: #E8E6DC; }
:global(.dark) .history-item { background: #2A2A2A; color: #E8E6DC; }
:global(.dark) .history-time { color: #B0AEA5; }
:global(.dark) .btn-primary-custom {
  background-color: #E8E6DC;
  border-color: #E8E6DC;
  color: #1D1D1D;
}
:global(.dark) .btn-primary-custom:hover {
  background-color: #E88B6F;
  border-color: #E88B6F;
  color: #FFFFFF;
}
:global(.dark) .el-input__wrapper,
:global(.dark) .el-select__wrapper {
  background-color: #0F0F0F;
  box-shadow: 0 0 0 1px #3A3A3A inset;
}
</style>
