<template>
  <div class="space-y-6">
    <!-- Scheduled Analyses for Favorites -->
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-3">
          <h3 class="text-lg font-semibold text-white">Kurzanalysen Favoriten</h3>
          <span class="badge badge-primary">{{ scheduledAnalyses.length }} Analysen</span>
          <span
            v-if="schedulerStatus.running"
            class="badge bg-green-500/20 text-green-400 text-xs"
          >
            Auto-Update aktiv
          </span>
        </div>
        <div class="flex items-center gap-2">
          <span v-if="schedulerStatus.last_run" class="text-xs text-gray-500">
            Zuletzt: {{ formatTimestamp(schedulerStatus.last_run) }}
          </span>
          <button
            @click="refreshAnalyses"
            :disabled="isRefreshing"
            class="btn btn-secondary text-sm flex items-center gap-1"
          >
            <span v-if="isRefreshing" class="animate-spin">&#8635;</span>
            <span v-else>&#8635;</span>
            Aktualisieren
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isRefreshing" class="text-center py-8">
        <div class="animate-spin text-2xl mb-2">&#8635;</div>
        <p class="text-gray-400">Analysiere Favoriten...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="scheduledAnalyses.length === 0" class="text-center py-8">
        <p class="text-gray-400 mb-2">Keine Analysen verfügbar</p>
        <p class="text-gray-500 text-sm">Markiere Symbole als Favoriten, um automatische Kurzanalysen zu erhalten.</p>
        <router-link to="/symbols" class="btn btn-primary mt-4">
          Symbole verwalten
        </router-link>
      </div>

      <!-- Analyses Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="analysis in sortedAnalyses"
          :key="analysis.symbol"
          class="bg-dark-300/50 rounded-lg p-4 hover:bg-dark-300 transition-colors cursor-pointer border border-gray-700/50"
          @click="goToAnalysis(analysis.symbol)"
        >
          <!-- Header -->
          <div class="flex justify-between items-start mb-3">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-yellow-400">★</span>
                <span class="font-semibold text-white text-lg">{{ analysis.symbol }}</span>
              </div>
              <span
                class="badge text-xs mt-1"
                :class="getCategoryBadgeClass(analysis.category)"
              >
                {{ analysis.category }}
              </span>
            </div>
            <div class="text-right">
              <span
                class="badge text-sm font-semibold"
                :class="getDirectionClass(analysis.direction)"
              >
                {{ analysis.direction }}
              </span>
            </div>
          </div>

          <!-- Confidence -->
          <div class="mb-3">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-400">Konfidenz</span>
              <span :class="getConfidenceTextClass(analysis.confidence_score)">
                {{ analysis.confidence_score }}%
              </span>
            </div>
            <div class="w-full bg-dark-400 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all"
                :class="getConfidenceBarClass(analysis.confidence_score)"
                :style="{ width: `${analysis.confidence_score}%` }"
              ></div>
            </div>
          </div>

          <!-- Key Prices -->
          <div class="grid grid-cols-2 gap-2 text-sm mb-3">
            <div v-if="analysis.entry_price">
              <span class="text-gray-500">Entry:</span>
              <span class="text-white ml-1">{{ formatPrice(analysis.entry_price) }}</span>
            </div>
            <div v-if="analysis.stop_loss">
              <span class="text-gray-500">SL:</span>
              <span class="text-red-400 ml-1">{{ formatPrice(analysis.stop_loss) }}</span>
            </div>
            <div v-if="analysis.take_profit_1">
              <span class="text-gray-500">TP1:</span>
              <span class="text-green-400 ml-1">{{ formatPrice(analysis.take_profit_1) }}</span>
            </div>
            <div v-if="analysis.risk_reward_ratio">
              <span class="text-gray-500">R/R:</span>
              <span class="text-blue-400 ml-1">{{ analysis.risk_reward_ratio.toFixed(2) }}</span>
            </div>
          </div>

          <!-- Technical Indicators (if available) -->
          <div v-if="analysis.indicators && Object.keys(analysis.indicators).length > 0" class="mb-3">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="(value, key) in getTopIndicators(analysis.indicators)"
                :key="key"
                class="text-xs bg-dark-400 px-2 py-0.5 rounded text-gray-300"
              >
                {{ key }}: {{ formatIndicator(value) }}
              </span>
            </div>
          </div>

          <!-- Rationale Preview -->
          <div v-if="analysis.rationale" class="text-xs text-gray-400 line-clamp-2">
            {{ analysis.rationale }}
          </div>

          <!-- Timestamp -->
          <div class="text-xs text-gray-500 mt-2 text-right">
            {{ formatTimestamp(analysis.analyzed_at) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Favorites Watchlist -->
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-3">
          <h3 class="text-lg font-semibold text-white">Favoriten Watchlist</h3>
          <span class="badge badge-primary">{{ sortedFavoriteSymbols.length }} Symbole</span>
        </div>
        <router-link to="/symbols" class="btn btn-secondary text-sm">
          Symbole verwalten
        </router-link>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-gray-700">
              <th class="text-left py-3 px-2">Symbol</th>
              <th class="text-left py-3 px-2">Kategorie</th>
              <th class="text-center py-3 px-2">Analyse</th>
              <th class="text-right py-3 px-2">Letzte Aktualisierung</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sym in sortedFavoriteSymbols"
              :key="sym.symbol"
              class="border-b border-gray-700/50 hover:bg-dark-300/50 cursor-pointer transition-colors"
              @click="selectFavoriteSymbol(sym)"
            >
              <td class="py-3 px-2">
                <div class="flex items-center gap-2">
                  <span class="text-yellow-400">★</span>
                  <span class="font-semibold text-white">{{ sym.symbol }}</span>
                </div>
              </td>
              <td class="py-3 px-2">
                <span
                  class="badge text-xs"
                  :class="getCategoryBadgeClass(sym.category)"
                >
                  {{ sym.category }}
                </span>
              </td>
              <td class="py-3 px-2 text-center">
                <span
                  v-if="getAnalysisForSymbol(sym.symbol)"
                  class="badge text-xs"
                  :class="getDirectionClass(getAnalysisForSymbol(sym.symbol).direction)"
                >
                  {{ getAnalysisForSymbol(sym.symbol).direction }}
                  ({{ getAnalysisForSymbol(sym.symbol).confidence_score }}%)
                </span>
                <span v-else class="text-gray-500 text-xs">-</span>
              </td>
              <td class="py-3 px-2 text-right text-gray-400 text-sm">
                {{ formatTimestamp(sym.last_data_timestamp) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()
const router = useRouter()
const isRefreshing = ref(false)

const favoriteSymbols = computed(() => store.favoriteSymbols)
const scheduledAnalyses = computed(() => store.scheduledAnalyses)
const schedulerStatus = computed(() => store.schedulerStatus)

// Sort favorites by category and then by symbol name
const sortedFavoriteSymbols = computed(() => {
  return [...favoriteSymbols.value].sort((a, b) => {
    const categoryCompare = (a.category || '').localeCompare(b.category || '')
    if (categoryCompare !== 0) return categoryCompare
    return (a.symbol || '').localeCompare(b.symbol || '')
  })
})

// Sort analyses by confidence (highest first), then by direction (LONG, SHORT, NEUTRAL)
const sortedAnalyses = computed(() => {
  return [...scheduledAnalyses.value].sort((a, b) => {
    // First by direction priority
    const dirPriority = { LONG: 0, SHORT: 1, NEUTRAL: 2 }
    const dirCompare = (dirPriority[a.direction] || 2) - (dirPriority[b.direction] || 2)
    if (dirCompare !== 0) return dirCompare
    // Then by confidence
    return (b.confidence_score || 0) - (a.confidence_score || 0)
  })
})

function getAnalysisForSymbol(symbol) {
  return scheduledAnalyses.value.find(a => a.symbol === symbol)
}

async function refreshAnalyses() {
  isRefreshing.value = true
  try {
    await store.runScheduledAnalysesNow()
  } finally {
    isRefreshing.value = false
  }
}

function selectFavoriteSymbol(sym) {
  store.setSelectedSymbol(sym.symbol)
  router.push('/analysis')
}

function goToAnalysis(symbol) {
  store.setSelectedSymbol(symbol)
  router.push('/analysis')
}

function getCategoryBadgeClass(category) {
  const classes = {
    crypto: 'bg-orange-500/20 text-orange-400',
    forex: 'bg-blue-500/20 text-blue-400',
    index: 'bg-purple-500/20 text-purple-400',
    commodity: 'bg-yellow-500/20 text-yellow-400',
    stock: 'bg-green-500/20 text-green-400',
    etf: 'bg-cyan-500/20 text-cyan-400',
    other: 'bg-gray-500/20 text-gray-400',
  }
  return classes[category] || classes.other
}

function getDirectionClass(direction) {
  if (direction === 'LONG') return 'bg-green-500/20 text-green-400'
  if (direction === 'SHORT') return 'bg-red-500/20 text-red-400'
  return 'bg-gray-500/20 text-gray-400'
}

function getConfidenceTextClass(score) {
  if (score >= 70) return 'text-green-400'
  if (score >= 50) return 'text-yellow-400'
  return 'text-red-400'
}

function getConfidenceBarClass(score) {
  if (score >= 70) return 'bg-green-500'
  if (score >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}

function formatTimestamp(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatPrice(price) {
  if (price == null) return '-'
  const num = parseFloat(price)
  if (num >= 1000) return num.toFixed(2)
  if (num >= 1) return num.toFixed(4)
  return num.toFixed(6)
}

function formatIndicator(value) {
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  return value
}

function getTopIndicators(indicators) {
  // Return only top 3 most important indicators
  const priority = ['RSI', 'Trend', 'Signal', 'MACD', 'SMA 200', 'BB Upper', 'BB Lower']
  const result = {}
  let count = 0

  for (const key of priority) {
    if (indicators[key] !== undefined && count < 3) {
      result[key] = indicators[key]
      count++
    }
  }

  return result
}

onMounted(async () => {
  // Fetch scheduled analyses on mount
  await store.fetchScheduledAnalyses()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
