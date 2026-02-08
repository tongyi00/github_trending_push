<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">Page Not Found</h2>
      <p class="error-description">
        The page you are looking for does not exist or has been moved.
      </p>
      <router-link to="/" class="back-home-btn">
        Back to Home
      </router-link>
    </div>
  </div>
</template>

<script setup>
// 404 Not Found page
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 2rem;
}

.not-found-content {
  max-width: 400px;
}

.error-code {
  font-size: 6rem;
  font-weight: 700;
  color: var(--el-color-primary);
  margin: 0;
  line-height: 1;
}

.error-title {
  font-size: 1.5rem;
  color: var(--el-text-color-primary);
  margin: 1rem 0;
}

.error-description {
  color: var(--el-text-color-secondary);
  margin-bottom: 2rem;
}

.back-home-btn {
  display: inline-block;
  padding: 0.75rem 2rem;
  background-color: var(--el-color-primary);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.back-home-btn:hover {
  background-color: var(--el-color-primary-dark-2);
}
</style>
