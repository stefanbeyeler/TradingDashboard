<template>
  <div class="min-h-screen bg-dark-400">
    <!-- Sidebar -->
    <aside class="fixed left-0 top-0 h-screen w-64 bg-dark-200 border-r border-gray-700 z-40">
      <!-- Logo -->
      <div class="h-16 flex items-center px-6 border-b border-gray-700">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-blue-600 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
            </svg>
          </div>
          <div>
            <h1 class="font-bold text-white text-lg">Trading</h1>
            <p class="text-xs text-gray-400">Dashboard</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="p-4 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-dark-100 hover:text-white transition-colors"
          :class="{ 'bg-primary-500/20 text-primary-400 border border-primary-500/30': $route.path === item.path }"
        >
          <component :is="item.icon" class="w-5 h-5" />
          <span>{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- System Status -->
      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
        <div class="flex items-center gap-2 mb-2">
          <div
            class="w-2 h-2 rounded-full"
            :class="systemHealthy ? 'bg-green-500' : 'bg-red-500'"
          ></div>
          <span class="text-sm text-gray-400">System Status</span>
        </div>
        <p class="text-xs text-gray-500">KI Trading Model: {{ kiStatus }}</p>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="ml-64">
      <!-- Header -->
      <header class="h-16 bg-dark-200 border-b border-gray-700 flex items-center justify-between px-6 sticky top-0 z-30">
        <div class="flex items-center gap-4">
          <h2 class="text-xl font-semibold text-white">{{ $route.name }}</h2>
        </div>
        <div class="flex items-center gap-4">
          <div class="text-right">
            <p class="text-sm text-gray-400">BTC Dominance</p>
            <p class="text-lg font-semibold text-white">{{ btcDominance }}%</p>
          </div>
          <div class="h-8 w-px bg-gray-700"></div>
          <div class="text-right">
            <p class="text-sm text-gray-400">Market Cap</p>
            <p class="text-lg font-semibold text-white">{{ formatMarketCap(totalMarketCap) }}</p>
          </div>
        </div>
      </header>

      <!-- Page Content -->
      <div class="p-6">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, h } from 'vue'
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()

// Navigation items with inline SVG icons
const navItems = [
  {
    name: 'Dashboard',
    path: '/',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' })
        ])
      }
    }
  },
  {
    name: 'KI Analysis',
    path: '/analysis',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' })
        ])
      }
    }
  },
  {
    name: 'Forecast',
    path: '/forecast',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z' })
        ])
      }
    }
  },
  {
    name: 'Symbols',
    path: '/symbols',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 6h16M4 10h16M4 14h16M4 18h16' })
        ])
      }
    }
  },
  {
    name: 'Markets',
    path: '/markets',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3' })
        ])
      }
    }
  },
  {
    name: 'News',
    path: '/news',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z' })
        ])
      }
    }
  },
  {
    name: 'Settings',
    path: '/settings',
    icon: {
      render() {
        return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z' })
        ])
      }
    }
  }
]

const systemHealthy = computed(() => store.systemStatus?.status === 'healthy')
const kiStatus = computed(() => {
  const services = store.systemStatus?.services
  if (!services) return 'unknown'
  // Check if all KI services are running
  const allServicesUp = services.llm_service && services.rag_service && services.nhits_service
  return allServicesUp ? 'healthy' : 'degraded'
})
const btcDominance = computed(() => store.btcDominance?.toFixed(1) || '0')
const totalMarketCap = computed(() => store.totalMarketCap || 0)

function formatMarketCap(value) {
  if (!value) return '$0'
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
  return `$${(value / 1e6).toFixed(2)}M`
}

onMounted(async () => {
  await Promise.all([
    store.fetchDashboard(),
    store.fetchGlobalData(),
    store.fetchKISymbols(),
  ])
})
</script>
