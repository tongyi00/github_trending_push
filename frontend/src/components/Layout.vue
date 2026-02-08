<script setup>
import { useTheme } from '../composables/useTheme'

// 使用主题组合式函数
const { isDark, toggleTheme } = useTheme()
</script>

<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <header class="top-navbar">
      <div class="navbar-content">
        <div class="navbar-left">
          <div class="logo-section">
            <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            <span class="logo-text">GitHub 趋势</span>
          </div>
          <nav class="main-nav">
            <router-link to="/" class="nav-link" active-class="active-link">
              <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
              </svg>
              首页
            </router-link>
            <router-link to="/analytics" class="nav-link" active-class="active-link">
              <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
              </svg>
              趋势分析
            </router-link>
            <router-link to="/settings" class="nav-link" active-class="active-link">
              <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/>
              </svg>
              配置
            </router-link>
          </nav>
        </div>
        <div class="navbar-right">
          <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
            <svg v-if="isDark" class="theme-icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
            </svg>
            <svg v-else class="theme-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #FAF9F5;
  color: #1D1D1D;
  transition: background-color 0.2s, color 0.2s;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'IBM Plex Sans', sans-serif;
}

/* 顶部导航栏 */
.top-navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #E8E6DC;
  transition: all 0.2s;
}

.navbar-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 24px;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 48px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.logo-icon {
  width: 24px;
  height: 24px;
  color: #D97757;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1D;
  white-space: nowrap;
  transition: color 0.2s;
}

.main-nav {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  color: #6B6B6B;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.nav-link:hover {
  color: #1D1D1D;
  background: #F3F2EE;
}

.nav-link.active-link {
  color: #D97757;
  background: #FFF5F0;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  padding: 0;
}

.theme-toggle:hover {
  background: #F3F2EE;
}

.theme-icon {
  width: 20px;
  height: 20px;
  color: #6B6B6B;
  transition: color 0.2s;
}

.theme-toggle:hover .theme-icon {
  color: #D97757;
}

/* 主内容区 */
.main-content {
  flex: 1;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* 深色模式 - Claude Aesthetic Dark */
:global(.dark) .layout-container {
  background-color: #0F0F0F;
  color: #E8E6DC;
}

:global(.dark) .top-navbar {
  background: rgba(15, 15, 15, 0.95);
  border-bottom-color: #2A2A2A;
}

:global(.dark) .logo-text {
  color: #E8E6DC;
}

:global(.dark) .nav-link {
  color: #B0AEA5;
}

:global(.dark) .nav-link:hover {
  color: #E8E6DC;
  background: #1A1A1A;
}

:global(.dark) .nav-link.active-link {
  color: #E88B6F;
  background: #2A1C18;
}

:global(.dark) .theme-toggle:hover {
  background: #1A1A1A;
}

:global(.dark) .theme-icon {
  color: #B0AEA5;
}

:global(.dark) .theme-toggle:hover .theme-icon {
  color: #E88B6F;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar-left {
    gap: 24px;
  }

  .main-nav {
    display: none;
  }

  .navbar-content {
    padding: 0 16px;
  }

  .main-content {
    padding: 24px 16px;
  }
}

@media (max-width: 640px) {
  .logo-text {
    font-size: 14px;
  }

  .logo-icon {
    width: 20px;
    height: 20px;
  }
}
</style>
