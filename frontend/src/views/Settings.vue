<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, startScheduler, stopScheduler, runTask, pollTaskUntilComplete } from '../api/scheduler'
import EmailConfig from '../components/settings/EmailConfig.vue'
import FilterConfig from '../components/settings/FilterConfig.vue'
import SchedulerConfig from '../components/settings/SchedulerConfig.vue'
import TaskHistoryConfig from '../components/settings/TaskHistoryConfig.vue'

const loading = ref(false)
const saving = ref(false)

// Settings data from API
const settings = reactive({
  email: { recipients: [] },
  scheduler: { timezone: 'Asia/Shanghai', daily_enabled: true, daily_time: '08:00', weekly_enabled: true, weekly_day: 'sunday', weekly_time: '22:00', monthly_enabled: true, monthly_time: '22:00' },
  filters: { min_stars: 100, min_stars_daily: 50, min_stars_weekly: 200, min_stars_monthly: 500 },
  subscription: { keywords: [], languages: [] },
  scheduler_running: false,
  next_run_times: {},
  task_history: []
})

const loadSettings = async () => {
  loading.value = true
  try {
    const data = await getSettings()
    Object.assign(settings, data)
  } catch (e) {
    console.error('Failed to load settings:', e)
    ElMessage.error('加载设置失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSettings()
})

const handleSave = async () => {
  saving.value = true
  try {
    const result = await updateSettings({
      email: settings.email,
      scheduler: settings.scheduler,
      filters: settings.filters,
      subscription: settings.subscription
    })
    if (result.success) {
      ElMessage.success('设置保存成功')
      await loadSettings()
    } else {
      ElMessage.error(result.message || '保存设置失败')
    }
  } catch (e) {
    ElMessage.error('保存设置时发生错误')
  } finally {
    saving.value = false
  }
}

const handleStartScheduler = async () => {
  try {
    const result = await startScheduler()
    if (result.success) {
      ElMessage.success('定时任务已启动')
      await loadSettings()
    } else {
      ElMessage.warning(result.message)
    }
  } catch (e) {
    ElMessage.error('启动定时任务失败')
  }
}

const handleStopScheduler = async () => {
  try {
    const result = await stopScheduler()
    if (result.success) {
      ElMessage.success('定时任务已停止')
      await loadSettings()
    } else {
      ElMessage.warning(result.message)
    }
  } catch (e) {
    ElMessage.error('停止定时任务失败')
  }
}

// 提交任务请求
const submitTask = async (taskType) => {
  const submitResult = await runTask(taskType)
  if (submitResult.status !== 'pending') {
    throw new Error(submitResult.message || '任务提交失败')
  }
  return submitResult.task_id
}

// 轮询任务进度
const pollTaskProgress = async (taskId) => {
  return await pollTaskUntilComplete(
    taskId,
    (status) => {
      // 进度回调（可选：在这里更新UI显示进度）
      if (status.status === 'running') {
        console.log('任务正在执行...')
      }
    },
    2000,  // 每2秒轮询一次
    300000 // 5分钟超时
  )
}

// 处理任务完成结果
const handleTaskResult = async (finalStatus) => {
  if (finalStatus.status === 'success') {
    const msg = `任务完成: 发现 ${finalStatus.repos_found} 个项目, 过滤后 ${finalStatus.repos_after_filter} 个` +
      (finalStatus.email_sent ? ', 邮件已发送' : '')
    ElMessage.success(msg)
  } else {
    throw new Error(finalStatus.error_message || '任务执行失败')
  }
  await loadSettings()
}

// 主处理函数
const handleRunTask = async (taskType, callback) => {
  try {
    ElMessage.info(`正在启动 ${taskType} 任务...`)

    // 1. 提交任务
    const taskId = await submitTask(taskType)
    ElMessage.info(`任务已提交 (ID: ${taskId})，正在执行...`)

    // 2. 轮询进度
    const finalStatus = await pollTaskProgress(taskId)

    // 3. 处理结果
    await handleTaskResult(finalStatus)

  } catch (e) {
    console.error(e)
    ElMessage.error(`任务错误: ${e.message || '未知错误'}`)
  } finally {
    if (callback) callback()
  }
}
</script>

<template>
  <div class="settings-container" v-loading="loading">
    <div class="settings-header">
      <h2>设置</h2>
      <p class="subtitle">配置热门项目偏好及定时</p>
    </div>

    <!-- Email Recipients -->
    <EmailConfig v-model="settings" />

    <!-- Subscription & Filters -->
    <FilterConfig v-model="settings" />

    <!-- Scheduler -->
    <SchedulerConfig
      v-model:scheduler="settings.scheduler"
      :scheduler-running="settings.scheduler_running"
      :next-run-times="settings.next_run_times"
      @start="handleStartScheduler"
      @stop="handleStopScheduler"
    />

    <!-- Task History & Manual Run -->
    <TaskHistoryConfig
      :task-history="settings.task_history"
      @run="handleRunTask"
    />

    <!-- Save Button -->
    <div class="save-actions">
      <el-button type="primary" size="large" @click="handleSave" :loading="saving" class="btn-primary-custom btn-large">保存</el-button>
    </div>
  </div>
</template>

<style scoped>
.settings-container { max-width: 900px; margin: 0 auto; padding: 20px; }
.settings-header { margin-bottom: 32px; }
.settings-header h2 { font-size: 24px; font-weight: 600; margin-bottom: 8px; color: #1D1D1D; letter-spacing: -0.01em; }
.subtitle { color: #6B6B6B; font-size: 14px; }

.save-actions { display: flex; justify-content: flex-end; margin-top: 30px; }

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
.btn-large {
  padding: 12px 24px;
  font-size: 14px;
}

/* Dark mode */
:global(.dark) .settings-header h2 { color: #E8E6DC; }
:global(.dark) .subtitle { color: #B0AEA5; }
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
</style>
