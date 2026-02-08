import { ref, onMounted, watch } from 'vue'

export function useTheme() {
  const isDark = ref(false)

  // Apply theme to document
  const applyTheme = () => {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Toggle theme function
  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  // Initialize theme
  onMounted(() => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      isDark.value = savedTheme === 'dark'
    } else {
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    applyTheme()
  })

  // Watch for changes and save to localStorage
  watch(isDark, (newValue) => {
    applyTheme()
    localStorage.setItem('theme', newValue ? 'dark' : 'light')
  })

  return {
    isDark,
    toggleTheme
  }
}
