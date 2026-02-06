<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useSubscriptionStore } from '../stores/subscription'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'

const subscriptionStore = useSubscriptionStore()
const { config, loading } = storeToRefs(subscriptionStore)
const submitting = ref(false)

// Form model to decouple from store until save
const form = reactive({
  keywords: [],
  min_stars: 0,
  languages: [],
  // We include other fields to preserve them if needed, or just partial update
  // Ideally we load these from the store
})

// Initialize form data when config is loaded
const initForm = () => {
  if (config.value) {
    form.keywords = [...(config.value.keywords || [])]
    form.min_stars = config.value.min_stars || 0
    form.languages = [...(config.value.languages || [])]
  }
}

onMounted(async () => {
  await subscriptionStore.fetchConfig()
  initForm()
})

const handleSave = async () => {
  submitting.value = true
  try {
    const success = await subscriptionStore.updateConfig({
      keywords: form.keywords,
      min_stars: form.min_stars,
      languages: form.languages
    })

    if (success) {
      ElMessage.success('Settings saved successfully')
    } else {
      ElMessage.error(subscriptionStore.error || 'Failed to save settings')
    }
  } catch (e) {
    ElMessage.error('An unexpected error occurred')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  initForm()
  ElMessage.info('Form reset to last saved state')
}
</script>

<template>
  <div class="settings-container">
    <div class="settings-header">
      <h2>Subscription Settings</h2>
      <p class="subtitle">Configure your trending project preferences</p>
    </div>

    <el-card class="settings-card" v-loading="loading">
      <el-form :model="form" label-position="top" class="settings-form">

        <!-- Keywords -->
        <el-form-item label="Keywords">
          <template #label>
            <div class="label-with-tip">
              <span>Keywords</span>
              <el-tooltip content="Filter projects containing these keywords in description or name" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-select
            v-model="form.keywords"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="Type and press Enter to add keywords (e.g., 'machine learning', 'react')"
            style="width: 100%"
          />
        </el-form-item>

        <!-- Min Stars -->
        <el-form-item label="Minimum Stars">
          <template #label>
            <div class="label-with-tip">
              <span>Minimum Stars</span>
              <el-tooltip content="Only show projects with at least this many stars" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-input-number
            v-model="form.min_stars"
            :min="0"
            :max="100000"
            :step="100"
            controls-position="right"
          />
        </el-form-item>

        <!-- Languages -->
        <el-form-item label="Programming Languages">
          <template #label>
            <div class="label-with-tip">
              <span>Languages</span>
              <el-tooltip content="Filter by specific programming languages" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <el-select
            v-model="form.languages"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="Type and press Enter to add languages (e.g., 'Python', 'Rust')"
            style="width: 100%"
          >
            <el-option label="Python" value="Python" />
            <el-option label="JavaScript" value="JavaScript" />
            <el-option label="TypeScript" value="TypeScript" />
            <el-option label="Go" value="Go" />
            <el-option label="Rust" value="Rust" />
            <el-option label="Java" value="Java" />
            <el-option label="C++" value="C++" />
          </el-select>
        </el-form-item>

        <!-- Actions -->
        <div class="form-actions">
          <el-button @click="handleReset">Reset</el-button>
          <el-button type="primary" @click="handleSave" :loading="submitting">Save Changes</el-button>
        </div>

      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
  margin-bottom: 24px;
}

.settings-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color-primary);
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-color-secondary);
  font-size: 14px;
}

.settings-card {
  border-radius: 8px;
}

.settings-form {
  padding: 10px 0;
}

.label-with-tip {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-icon {
  color: var(--text-color-secondary);
  cursor: help;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 32px;
  gap: 12px;
}
</style>
