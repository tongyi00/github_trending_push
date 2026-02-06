<script setup>
import { onMounted } from 'vue'
import { useTrendingStore } from '../stores/trending'
import { useSubscriptionStore } from '../stores/subscription'

const trendingStore = useTrendingStore()
const subscriptionStore = useSubscriptionStore()

onMounted(async () => {
  await trendingStore.fetchTrending()
  await subscriptionStore.fetchConfig()
})
</script>

<template>
  <div class="store-test">
    <h2>Trending Store Test</h2>
    <div v-if="trendingStore.loading">Loading trending data...</div>
    <div v-else>
      <p>Projects count: {{ trendingStore.projects.length }}</p>
      <ul>
        <li v-for="project in trendingStore.projects" :key="project.name">
          {{ project.name }} ({{ project.stars }} stars)
        </li>
      </ul>
      <p>Stats: Total Stars {{ trendingStore.stats.totalStars }}</p>
    </div>

    <h2>Subscription Store Test</h2>
    <div v-if="subscriptionStore.loading">Loading config...</div>
    <div v-else>
      <p>Scheduler: {{ subscriptionStore.config.scheduler }}</p>
      <p>Keywords: {{ subscriptionStore.config.keywords.join(', ') }}</p>
    </div>
  </div>
</template>

<style scoped>
.store-test {
  border: 1px solid #ddd;
  padding: 20px;
  margin: 20px;
  border-radius: 8px;
}
</style>
