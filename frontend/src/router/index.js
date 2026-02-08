import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Dashboard
  },
  {
    path: '/project/:owner/:name',
    name: 'ProjectDetail',
    component: () => import('../views/ProjectDetail.vue')
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('../views/Analytics.vue')
  },
  {
    path: '/analysis/:owner/:name',
    name: 'AnalysisReport',
    component: () => import('../views/AnalysisReport.vue'),
    props: route => ({
      owner: route.params.owner,
      name: route.params.name,
      ...route.query
    })
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: 'Page Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for setting title
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - GitHub Trending` : 'GitHub Trending Push';
  next();
});

// Error handling
router.onError((error) => {
  console.error('Router error:', error);
  // Handle dynamic import failures (ChunkLoadError)
  if (error.message.includes('Failed to fetch dynamically imported module') || error.message.includes('Importing a module script failed')) {
    if (!localStorage.getItem('router_reload')) {
      localStorage.setItem('router_reload', 'true');
      window.location.reload();
    } else {
      localStorage.removeItem('router_reload');
    }
  }
});

export default router
