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
      <span class="card-title">邮件通知</span>
    </template>
    <el-form label-position="top" class="settings-form">
      <el-form-item label="收件人列表">
        <el-select
          v-model="modelValue.email.recipients"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="添加收件人邮箱..."
          style="width: 100%"
        >
          <template #tag="{ value }">
            <el-tag :key="value" closable type="info" effect="light">
              {{ value }}
            </el-tag>
          </template>
        </el-select>
        <div class="form-tip">输入邮箱地址后按回车添加，支持多个收件人</div>
      </el-form-item>
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

.form-tip {
  font-size: 12px;
  color: #6B6B6B;
  margin-top: 8px;
}

:global(.dark) .settings-card {
  background: #1A1A1A;
  border-color: #2A2A2A;
}
:global(.dark) .settings-card :deep(.el-card__header) {
  border-bottom-color: #2A2A2A;
}
:global(.dark) .card-title { color: #E8E6DC; }
:global(.dark) .form-tip { color: #B0AEA5; }
:global(.dark) .el-input__wrapper,
:global(.dark) .el-select__wrapper {
  background-color: #0F0F0F;
  box-shadow: 0 0 0 1px #3A3A3A inset;
}
</style>
