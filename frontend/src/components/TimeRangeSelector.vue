<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true
  },
  options: {
    type: Array,
    required: true,
    // Expected format: [{ label: 'Daily', value: 'daily' }, ...]
    default: () => [
      { label: 'Daily', value: 'daily' },
      { label: 'Weekly', value: 'weekly' },
      { label: 'Monthly', value: 'monthly' }
    ]
  }
});

defineEmits(['update:modelValue']);
</script>

<template>
  <div class="time-range-selector">
    <button
      v-for="option in options"
      :key="option.value"
      class="range-btn"
      :class="{ active: modelValue === option.value }"
      @click="$emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<style scoped>
.time-range-selector {
  display: inline-flex;
  background: #f0f2f5;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.range-btn {
  background: transparent;
  border: none;
  padding: 8px 16px;
  font-size: 0.9em;
  color: #666;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.range-btn:hover {
  color: #333;
  background: rgba(0,0,0,0.05);
}

.range-btn.active {
  background: #ffffff;
  color: #646cff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  font-weight: 600;
}

@media (prefers-color-scheme: dark) {
  .time-range-selector {
    background: #2a2a2a;
  }

  .range-btn {
    color: #aaa;
  }

  .range-btn:hover {
    color: #fff;
    background: rgba(255,255,255,0.05);
  }

  .range-btn.active {
    background: #1a1a1a;
    color: #747bff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
}
</style>
