<template>
  <div class="skeleton-card">
    <div class="skeleton-header">
      <div class="skeleton-title"></div>
      <div class="skeleton-badge"></div>
    </div>
    <div class="skeleton-text"></div>
    <div class="skeleton-text"></div>
    <div class="skeleton-text short"></div>
    <div class="skeleton-stats">
      <div class="skeleton-stat"></div>
      <div class="skeleton-stat"></div>
      <div class="skeleton-stat"></div>
    </div>
    <div class="skeleton-footer">
      <div class="skeleton-tag"></div>
      <div class="skeleton-buttons">
        <div class="skeleton-button"></div>
        <div class="skeleton-button"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.skeleton-title {
  flex: 1;
  height: 24px;
  background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 6px;
  max-width: 60%;
}

.skeleton-badge {
  width: 70px;
  height: 28px;
  background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 8px;
  flex-shrink: 0;
}

.skeleton-text {
  width: 100%;
  height: 16px;
  background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

.skeleton-text.short {
  width: 75%;
}

.skeleton-stats {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid #f3f4f6;
  border-bottom: 1px solid #f3f4f6;
}

.skeleton-stat {
  width: 90px;
  height: 18px;
  background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

.skeleton-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.skeleton-tag {
  width: 90px;
  height: 20px;
  background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 6px;
}

.skeleton-buttons {
  display: flex;
  gap: 8px;
}

.skeleton-button {
  width: 80px;
  height: 36px;
  background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 50%, #f3f4f6 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* 深色模式 */
:global(.dark) .skeleton-card {
  background: #1f2937;
  border-color: #374151;
}

:global(.dark) .skeleton-title,
:global(.dark) .skeleton-badge,
:global(.dark) .skeleton-text,
:global(.dark) .skeleton-stat,
:global(.dark) .skeleton-tag,
:global(.dark) .skeleton-button {
  background: linear-gradient(90deg, #1f2937 0%, #374151 50%, #1f2937 100%);
  background-size: 200% 100%;
}

:global(.dark) .skeleton-stats {
  border-top-color: #374151;
  border-bottom-color: #374151;
}

/* 移动端优化 */
@media (max-width: 640px) {
  .skeleton-card {
    padding: 16px;
  }

  .skeleton-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .skeleton-title {
    max-width: 100%;
  }

  .skeleton-badge {
    align-self: flex-start;
  }

  .skeleton-buttons {
    width: 100%;
  }

  .skeleton-button {
    flex: 1;
  }
}
</style>
