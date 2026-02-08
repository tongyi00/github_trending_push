import request from './index'

export interface EmailSettings {
  smtp_server: string
  smtp_port: number
  use_ssl: boolean
  sender: string | null
  password: string | null
  recipients: string[]
}

export interface SchedulerSettings {
  timezone: string
  daily_enabled: boolean
  daily_time: string
  weekly_enabled: boolean
  weekly_day: string
  weekly_time: string
  monthly_enabled: boolean
  monthly_time: string
}

export interface FilterSettings {
  min_stars: number
  min_stars_daily: number
  min_stars_weekly: number
  min_stars_monthly: number
}

export interface SubscriptionSettings {
  keywords: string[]
  languages: string[]
}

export interface TaskHistoryItem {
  id: number
  task_type: string
  started_at: string
  finished_at: string | null
  status: string
  error_message: string | null
}

export interface SettingsResponse {
  email: EmailSettings
  scheduler: SchedulerSettings
  filters: FilterSettings
  subscription: SubscriptionSettings
  scheduler_running: boolean
  next_run_times: Record<string, string | null>
  task_history: TaskHistoryItem[]
}

export interface SettingsUpdateRequest {
  email?: EmailSettings
  scheduler?: SchedulerSettings
  filters?: FilterSettings
  subscription?: SubscriptionSettings
}

export interface TaskRunResult {
  task_id: string
  task_type: string
  status: string
  message: string
}

export interface TaskStatusResponse {
  task_id: string
  task_type: string
  status: string
  started_at: string | null
  finished_at: string | null
  repos_found: number
  repos_after_filter: number
  email_sent: boolean
  error_message: string | null
}

export async function getSettings(): Promise<SettingsResponse> {
  const response = await request.get('/api/settings')
  return response.data
}

export async function updateSettings(settings: SettingsUpdateRequest): Promise<{ success: boolean; message: string }> {
  const response = await request.put('/api/settings', settings)
  return response.data
}

export async function startScheduler(): Promise<{ success: boolean; message: string }> {
  const response = await request.put('/api/scheduler', { status: 'running' })
  return response.data
}

export async function stopScheduler(): Promise<{ success: boolean; message: string }> {
  const response = await request.put('/api/scheduler', { status: 'stopped' })
  return response.data
}

export async function runTask(taskType: string): Promise<TaskRunResult> {
  const response = await request.post('/api/tasks/run', { task_type: taskType })
  return response.data
}

export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  const response = await request.get(`/api/tasks/status/${taskId}`)
  return response.data
}

/**
 * 轮询任务状态直到完成（成功或失败）
 * @param taskId 任务ID
 * @param onProgress 进度回调（可选）
 * @param interval 轮询间隔（毫秒，默认2000ms）
 * @param timeout 超时时间（毫秒，默认5分钟）
 */
export async function pollTaskUntilComplete(
  taskId: string,
  onProgress?: (status: TaskStatusResponse) => void,
  interval: number = 2000,
  timeout: number = 300000
): Promise<TaskStatusResponse> {
  const startTime = Date.now()

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getTaskStatus(taskId)

        // 调用进度回调
        if (onProgress) {
          onProgress(status)
        }

        // 检查任务是否完成
        if (status.status === 'success' || status.status === 'failed') {
          resolve(status)
          return
        }

        // 检查是否超时
        if (Date.now() - startTime > timeout) {
          reject(new Error('Task polling timeout'))
          return
        }

        // 继续轮询
        setTimeout(poll, interval)
      } catch (error) {
        reject(error)
      }
    }

    poll()
  })
}
