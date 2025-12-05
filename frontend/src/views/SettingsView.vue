<template>
  <div class="space-y-6">
    <!-- System Status -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">System Status</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="(status, service) in services"
          :key="service"
          class="bg-dark-300 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-400 capitalize">{{ service }}</span>
            <span
              class="w-3 h-3 rounded-full"
              :class="{
                'bg-green-500': status === 'healthy',
                'bg-yellow-500': status === 'degraded',
                'bg-red-500': status === 'unhealthy' || status === 'unavailable',
                'bg-gray-500': status === 'unknown' || status === 'not_configured'
              }"
            ></span>
          </div>
          <p class="text-white font-medium capitalize">{{ status }}</p>
        </div>
      </div>
      <button @click="refreshHealth" :disabled="loading" class="btn btn-secondary mt-4">
        {{ loading ? 'Checking...' : 'Refresh Status' }}
      </button>
    </div>

    <!-- API Configuration -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">API Configuration</h3>
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-sm text-gray-400 block mb-1">KITradingModel API URL</label>
            <input
              type="text"
              :value="config.kitradingUrl"
              disabled
              class="input bg-dark-400"
            />
            <p class="text-xs text-gray-500 mt-1">Configured via backend .env</p>
          </div>
          <div>
            <label class="text-sm text-gray-400 block mb-1">Dashboard API Port</label>
            <input
              type="text"
              value="3010"
              disabled
              class="input bg-dark-400"
            />
            <p class="text-xs text-gray-500 mt-1">Backend server port</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Trading Strategies -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Available Trading Strategies</h3>
      <div v-if="strategies.length" class="space-y-3">
        <div
          v-for="strategy in strategies"
          :key="strategy.id"
          class="flex items-center justify-between p-4 bg-dark-300 rounded-lg"
        >
          <div>
            <h4 class="text-white font-medium">{{ strategy.name }}</h4>
            <p class="text-sm text-gray-400">{{ strategy.type }} | Risk: {{ strategy.risk_level }}</p>
          </div>
          <span
            v-if="strategy.is_default"
            class="badge badge-success"
          >
            Default
          </span>
        </div>
      </div>
      <p v-else class="text-gray-500">No strategies configured</p>
    </div>

    <!-- Forecast Models -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">NHITS Forecast Models</h3>
      <div v-if="forecastModels.length" class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-gray-700">
              <th class="text-left py-2">Symbol</th>
              <th class="text-center py-2">Status</th>
              <th class="text-right py-2">Last Trained</th>
              <th class="text-right py-2">Samples</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="model in forecastModels" :key="model.symbol" class="border-b border-gray-700/50">
              <td class="py-2 text-white">{{ model.symbol }}</td>
              <td class="py-2 text-center">
                <span
                  class="badge"
                  :class="model.model_exists ? 'badge-success' : 'badge-warning'"
                >
                  {{ model.model_exists ? 'Ready' : 'Not Trained' }}
                </span>
              </td>
              <td class="py-2 text-right text-gray-400">
                {{ model.last_trained ? formatDate(model.last_trained) : 'Never' }}
              </td>
              <td class="py-2 text-right text-gray-400">
                {{ model.training_samples || 'N/A' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-gray-500">No forecast models available</p>
    </div>

    <!-- Watchlist Settings -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Default Watchlist</h3>
      <div>
        <label class="text-sm text-gray-400 block mb-1">Symbols (comma-separated)</label>
        <input
          v-model="watchlistInput"
          type="text"
          class="input"
          placeholder="BTC,ETH,SOL,XRP"
        />
        <p class="text-xs text-gray-500 mt-1">These symbols will be shown on the dashboard</p>
      </div>
      <button @click="saveWatchlist" class="btn btn-primary mt-4">
        Save Watchlist
      </button>
    </div>

    <!-- About -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">About</h3>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-400">Dashboard Version</span>
          <span class="text-white">1.0.0</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">Frontend</span>
          <span class="text-white">Vue 3 + Vite + TailwindCSS</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">Backend</span>
          <span class="text-white">FastAPI + Python</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">External APIs</span>
          <span class="text-white">CoinGecko, Binance, Alpha Vantage</span>
        </div>
      </div>

      <div class="mt-6 pt-4 border-t border-gray-700">
        <h4 class="text-white font-medium mb-2">API Documentation</h4>
        <div class="flex gap-2">
          <a
            href="/api/docs"
            target="_blank"
            class="btn btn-secondary text-sm"
          >
            Swagger UI
          </a>
          <a
            href="/api/redoc"
            target="_blank"
            class="btn btn-secondary text-sm"
          >
            ReDoc
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMarketStore } from '@/stores/market'
import * as api from '@/services/api'

const store = useMarketStore()
const loading = ref(false)
const services = ref({})
const watchlistInput = ref('BTC,ETH,SOL,XRP,BNB,ADA,DOGE,AVAX')

const strategies = computed(() => store.kiStrategies)
const forecastModels = computed(() => store.forecastModels)

const config = {
  kitradingUrl: 'http://localhost:3011/api/v1',
}

async function refreshHealth() {
  loading.value = true
  try {
    const health = await api.getHealth()
    services.value = health.services || {}
  } catch (e) {
    console.error('Failed to refresh health:', e)
  } finally {
    loading.value = false
  }
}

function saveWatchlist() {
  localStorage.setItem('watchlist', watchlistInput.value)
  store.fetchDashboard(watchlistInput.value)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('de-DE')
}

onMounted(async () => {
  // Load saved watchlist
  const saved = localStorage.getItem('watchlist')
  if (saved) {
    watchlistInput.value = saved
  }

  await Promise.all([
    refreshHealth(),
    store.fetchKIStrategies(),
    store.fetchForecastModels(),
  ])
})
</script>
