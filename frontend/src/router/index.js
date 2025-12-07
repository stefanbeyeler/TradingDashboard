import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/AnalysisView.vue'),
  },
  {
    path: '/forecast',
    name: 'Forecast',
    component: () => import('@/views/ForecastView.vue'),
  },
  {
    path: '/symbols',
    name: 'Symbols',
    component: () => import('@/views/SymbolsView.vue'),
  },
  {
    path: '/markets',
    name: 'Markets',
    component: () => import('@/views/MarketsView.vue'),
  },
  {
    path: '/news',
    name: 'News',
    component: () => import('@/views/NewsView.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
