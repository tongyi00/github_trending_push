<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <el-card class="settings-card">
    <template #header>
      <span class="card-title">筛选 & 订阅</span>
    </template>
    <el-form label-position="top" class="settings-form">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="关键字">
            <el-select
              v-model="modelValue.subscription.keywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="添加关键字..."
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="语言">
            <el-select
              v-model="modelValue.subscription.languages"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="添加语言"
              style="width: 100%"
            >
              <el-option label="Python" value="Python" />
              <el-option label="JavaScript" value="JavaScript" />
              <el-option label="TypeScript" value="TypeScript" />
              <el-option label="Go" value="Go" />
              <el-option label="Rust" value="Rust" />
              <el-option label="Java" value="Java" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-form-item label="最低 Stars">
            <el-input-number v-model="modelValue.filters.min_stars" :min="0" :step="50" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="日榜最低 Stars">
            <el-input-number v-model="modelValue.filters.min_stars_daily" :min="0" :step="10" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="周榜最低 Stars">
            <el-input-number v-model="modelValue.filters.min_stars_weekly" :min="0" :step="50" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="月榜最低 Stars">
            <el-input-number v-model="modelValue.filters.min_stars_monthly" :min="0" :step="100" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
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
.settings-form { padding: 10px 0; }

:global(.dark) .settings-card {
  background: #1A1A1A;
  border-color: #2A2A2A;
}
:global(.dark) .settings-card :deep(.el-card__header) {
  border-bottom-color: #2A2A2A;
}
:global(.dark) .card-title { color: #E8E6DC; }
:global(.dark) .el-input__wrapper,
:global(.dark) .el-select__wrapper {
  background-color: #0F0F0F;
  box-shadow: 0 0 0 1px #3A3A3A inset;
}
</style>
