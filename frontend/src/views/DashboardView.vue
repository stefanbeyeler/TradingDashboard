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

      <!-- Analyses Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-gray-700">
              <th
                v-for="col in columns"
                :key="col.key"
                class="py-3 px-2 cursor-pointer hover:text-white transition-colors select-none"
                :class="col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'"
                @click="toggleSort(col.key)"
              >
                <div class="flex items-center gap-1" :class="col.align === 'right' ? 'justify-end' : col.align === 'center' ? 'justify-center' : ''">
                  <span>{{ col.label }}</span>
                  <span v-if="sortKey === col.key" class="text-primary-400">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                  <span v-else class="text-gray-600 text-xs">⇅</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="analysis in sortedAnalyses"
              :key="analysis.symbol"
              class="border-b border-gray-700/50 hover:bg-dark-300/50 cursor-pointer transition-colors"
              @click="goToAnalysis(analysis.symbol)"
            >
              <!-- Symbol -->
              <td class="py-3 px-2">
                <div class="flex items-center gap-2">
                  <span class="text-yellow-400">★</span>
                  <span class="font-semibold text-white">{{ analysis.symbol }}</span>
                </div>
              </td>

              <!-- Category -->
              <td class="py-3 px-2">
                <span
                  class="badge text-xs"
                  :class="getCategoryBadgeClass(analysis.category)"
                >
                  {{ analysis.category }}
                </span>
              </td>

              <!-- Direction/Signal -->
              <td class="py-3 px-2 text-center">
                <span
                  class="badge text-xs font-semibold"
                  :class="getDirectionClass(analysis.direction)"
                >
                  {{ analysis.direction }}
                </span>
              </td>

              <!-- Confidence -->
              <td class="py-3 px-2">
                <div class="flex items-center gap-2">
                  <div class="w-16 bg-dark-400 rounded-full h-2">
                    <div
                      class="h-2 rounded-full transition-all"
                      :class="getConfidenceBarClass(analysis.confidence_score)"
                      :style="{ width: `${analysis.confidence_score}%` }"
                    ></div>
                  </div>
                  <span
                    class="text-xs font-medium"
                    :class="getConfidenceTextClass(analysis.confidence_score)"
                  >
                    {{ analysis.confidence_score }}%
                  </span>
                </div>
              </td>

              <!-- Entry Price -->
              <td class="py-3 px-2 text-right text-white">
                {{ analysis.entry_price ? formatPrice(analysis.entry_price) : '-' }}
              </td>

              <!-- Stop Loss -->
              <td class="py-3 px-2 text-right">
                <span :class="analysis.stop_loss && analysis.stop_loss > 0 ? 'text-red-400' : 'text-gray-500'">
                  {{ analysis.stop_loss && analysis.stop_loss > 0 ? formatPrice(analysis.stop_loss) : '-' }}
                </span>
              </td>

              <!-- Take Profit -->
              <td class="py-3 px-2 text-right">
                <span :class="analysis.take_profit_1 ? 'text-green-400' : 'text-gray-500'">
                  {{ analysis.take_profit_1 ? formatPrice(analysis.take_profit_1) : '-' }}
                </span>
              </td>

              <!-- Risk/Reward -->
              <td class="py-3 px-2 text-center">
                <span :class="analysis.risk_reward_ratio ? 'text-blue-400' : 'text-gray-500'">
                  {{ analysis.risk_reward_ratio ? analysis.risk_reward_ratio.toFixed(1) : '-' }}
                </span>
              </td>

              <!-- RSI -->
              <td class="py-3 px-2 text-center">
                <span :class="getRsiClass(analysis.indicators?.RSI)">
                  {{ analysis.indicators?.RSI ? analysis.indicators.RSI.toFixed(1) : '-' }}
                </span>
              </td>

              <!-- Trend -->
              <td class="py-3 px-2 text-center">
                <span
                  v-if="analysis.indicators?.Trend"
                  class="text-xs"
                  :class="getTrendClass(analysis.indicators.Trend)"
                >
                  {{ formatTrend(analysis.indicators.Trend) }}
                </span>
                <span v-else class="text-gray-500">-</span>
              </td>

              <!-- Timestamp -->
              <td class="py-3 px-2 text-right text-gray-400 text-xs">
                {{ formatTimestamp(analysis.analyzed_at) }}
              </td>
            </tr>
          </tbody>
        </table>
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

// Sorting state
const sortKey = ref('direction')
const sortDirection = ref('asc')

// Column definitions
const columns = [
  { key: 'symbol', label: 'Symbol', align: 'left' },
  { key: 'category', label: 'Kategorie', align: 'left' },
  { key: 'direction', label: 'Signal', align: 'center' },
  { key: 'confidence_score', label: 'Konfidenz', align: 'center' },
  { key: 'entry_price', label: 'Entry', align: 'right' },
  { key: 'stop_loss', label: 'Stop Loss', align: 'right' },
  { key: 'take_profit_1', label: 'Take Profit', align: 'right' },
  { key: 'risk_reward_ratio', label: 'R/R', align: 'center' },
  { key: 'rsi', label: 'RSI', align: 'center' },
  { key: 'trend', label: 'Trend', align: 'center' },
  { key: 'analyzed_at', label: 'Zeit', align: 'right' },
]

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

// Toggle sort direction or change sort key
function toggleSort(key) {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

// Get sortable value for a given key
function getSortValue(analysis, key) {
  switch (key) {
    case 'symbol':
      return analysis.symbol || ''
    case 'category':
      return analysis.category || ''
    case 'direction':
      // LONG=0, SHORT=1, NEUTRAL=2 for sorting
      const dirPriority = { LONG: 0, SHORT: 1, NEUTRAL: 2 }
      return dirPriority[analysis.direction] ?? 3
    case 'confidence_score':
      return analysis.confidence_score || 0
    case 'entry_price':
      return analysis.entry_price || 0
    case 'stop_loss':
      return analysis.stop_loss && analysis.stop_loss > 0 ? analysis.stop_loss : 0
    case 'take_profit_1':
      return analysis.take_profit_1 || 0
    case 'risk_reward_ratio':
      return analysis.risk_reward_ratio || 0
    case 'rsi':
      return analysis.indicators?.RSI || 0
    case 'trend':
      // Uptrend=0, Downtrend=1, other=2 for sorting
      const trend = analysis.indicators?.Trend?.toLowerCase() || ''
      if (trend.includes('uptrend')) return 0
      if (trend.includes('downtrend')) return 1
      return 2
    case 'analyzed_at':
      return analysis.analyzed_at ? new Date(analysis.analyzed_at).getTime() : 0
    default:
      return 0
  }
}

// Sort analyses based on current sort settings
const sortedAnalyses = computed(() => {
  const data = [...scheduledAnalyses.value]
  const key = sortKey.value
  const dir = sortDirection.value

  return data.sort((a, b) => {
    const valA = getSortValue(a, key)
    const valB = getSortValue(b, key)

    let comparison = 0
    if (typeof valA === 'string' && typeof valB === 'string') {
      comparison = valA.localeCompare(valB)
    } else {
      comparison = valA - valB
    }

    return dir === 'asc' ? comparison : -comparison
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

function getRsiClass(rsi) {
  if (!rsi) return 'text-gray-500'
  if (rsi >= 70) return 'text-red-400'  // Overbought
  if (rsi <= 30) return 'text-green-400'  // Oversold
  return 'text-white'
}

function getTrendClass(trend) {
  if (!trend) return 'text-gray-500'
  const t = trend.toLowerCase()
  if (t.includes('uptrend') || t.includes('bullish')) return 'text-green-400'
  if (t.includes('downtrend') || t.includes('bearish')) return 'text-red-400'
  return 'text-yellow-400'
}

function formatTrend(trend) {
  if (!trend) return '-'
  // Shorten trend names for table display
  return trend
    .replace('Strong_', '')
    .replace('_', ' ')
    .replace('uptrend', 'Up')
    .replace('downtrend', 'Down')
    .replace('Uptrend', 'Up')
    .replace('Downtrend', 'Down')
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
  if (Math.abs(num) >= 1000) return num.toFixed(2)
  if (Math.abs(num) >= 1) return num.toFixed(4)
  return num.toFixed(6)
}

onMounted(async () => {
  // Fetch scheduled analyses on mount
  await store.fetchScheduledAnalyses()
})
</script>
