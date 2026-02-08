<script setup>
const props = defineProps({
  scheduler: {
    type: Object,
    required: true
  },
  schedulerRunning: {
    type: Boolean,
    default: false
  },
  nextRunTimes: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:scheduler', 'start', 'stop'])

const weekDays = [
  { label: 'Monday', value: 'monday' },
  { label: 'Tuesday', value: 'tuesday' },
  { label: 'Wednesday', value: 'wednesday' },
  { label: 'Thursday', value: 'thursday' },
  { label: 'Friday', value: 'friday' },
  { label: 'Saturday', value: 'saturday' },
  { label: 'Sunday', value: 'sunday' }
]

const formatDateTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const handleStart = () => emit('start')
const handleStop = () => emit('stop')
</script>

<template>
  <el-card class="settings-card">
    <template #header>
      <span class="card-title">定时推送</span>
    </template>

    <div class="scheduler-status">
      <div class="status-row">
        <span class="status-label">状态:</span>
        <el-tag :type="schedulerRunning ? 'success' : 'info'" size="small" effect="plain" class="status-tag">
          {{ schedulerRunning ? '运行中' : '关闭' }}
        </el-tag>
        <div class="status-actions">
          <el-button size="small" @click="handleStop" :disabled="!schedulerRunning">暂停</el-button>
          <el-button size="small" type="primary" @click="handleStart" :disabled="schedulerRunning" class="btn-primary-custom">启动</el-button>
        </div>
      </div>
    </div>

    <el-divider />
    <div class="task-schedules">
      <div class="schedule-item">
        <div class="schedule-left">
          <el-switch v-model="scheduler.daily_enabled" size="small" active-color="#D97757" />
          <span class="task-name">日榜</span>
        </div>
        <div class="schedule-center">
          <span class="schedule-label">时间:</span>
          <el-time-picker v-model="scheduler.daily_time" format="HH:mm" value-format="HH:mm" :clearable="false" size="small" style="width: 100px" />
        </div>
        <div class="schedule-right">
          <span class="next-run">下次运行 {{ formatDateTime(nextRunTimes?.daily) }}</span>
        </div>
      </div>

      <div class="schedule-item">
        <div class="schedule-left">
          <el-switch v-model="scheduler.weekly_enabled" size="small" active-color="#D97757" />
          <span class="task-name">周榜</span>
        </div>
        <div class="schedule-center">
          <el-select v-model="scheduler.weekly_day" size="small" style="width: 110px">
            <el-option v-for="day in weekDays" :key="day.value" :label="day.label" :value="day.value" />
          </el-select>
          <el-time-picker v-model="scheduler.weekly_time" format="HH:mm" value-format="HH:mm" :clearable="false" size="small" style="width: 100px" />
        </div>
        <div class="schedule-right">
          <span class="next-run">下次运行 {{ formatDateTime(nextRunTimes?.weekly) }}</span>
        </div>
      </div>

      <div class="schedule-item">
        <div class="schedule-left">
          <el-switch v-model="scheduler.monthly_enabled" size="small" active-color="#D97757" />
          <span class="task-name">月榜</span>
        </div>
        <div class="schedule-center">
          <span class="schedule-label">每月最后一天:</span>
          <el-time-picker v-model="scheduler.monthly_time" format="HH:mm" value-format="HH:mm" :clearable="false" size="small" style="width: 100px" />
        </div>
        <div class="schedule-right">
          <span class="next-run">下次运行 {{ formatDateTime(nextRunTimes?.monthly) }}</span>
        </div>
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

.scheduler-status { margin-bottom: 16px; }
.status-row { display: flex; align-items: center; gap: 12px; }
.status-label { font-weight: 500; color: #1D1D1D; }
.status-actions { margin-left: auto; display: flex; gap: 8px; }

.task-schedules { display: flex; flex-direction: column; gap: 12px; }
.schedule-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #F7F6F2;
  border-radius: 8px;
  gap: 16px;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.schedule-item:hover {
  border-color: #E8E6DC;
  background: #F3F2EE;
}

.schedule-left { display: flex; align-items: center; gap: 10px; min-width: 120px; }
.schedule-center { display: flex; align-items: center; gap: 8px; flex: 1; }
.schedule-label { color: #6B6B6B; font-size: 13px; }
.schedule-right { display: flex; align-items: center; gap: 12px; }
.task-name { font-weight: 600; color: #1D1D1D; }
.next-run { color: #6B6B6B; font-size: 13px; min-width: 140px; text-align: right; }

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
.btn-primary-custom:disabled,
.btn-primary-custom.is-disabled,
.btn-primary-custom:disabled:hover,
.btn-primary-custom.is-disabled:hover {
  background-color: #F3F2EE;
  border-color: #E8E6DC;
  color: #B0AEA5;
  cursor: not-allowed;
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
:global(.dark) .status-label { color: #E8E6DC; }
:global(.dark) .schedule-item { background: #2A1C18; }
:global(.dark) .schedule-item:hover { background: #35241E; border-color: #4A2E26; }
:global(.dark) .task-name { color: #E8E6DC; }
:global(.dark) .schedule-label { color: #B0AEA5; }
:global(.dark) .next-run { color: #B0AEA5; }
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
:global(.dark) .btn-primary-custom:disabled,
:global(.dark) .btn-primary-custom.is-disabled {
  background-color: #2A2A2A;
  border-color: #3A3A3A;
  color: #555555;
  cursor: not-allowed;
}
:global(.dark) .el-input__wrapper,
:global(.dark) .el-select__wrapper {
  background-color: #0F0F0F;
  box-shadow: 0 0 0 1px #3A3A3A inset;
}
</style>
