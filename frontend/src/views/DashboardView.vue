<template>
  <div class="space-y-6">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Gesamt Symbole</p>
        <p class="text-2xl font-bold text-white">{{ symbolStats.total_symbols || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">Verfügbare Assets</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Mit Daten</p>
        <p class="text-2xl font-bold text-green-400">{{ symbolStats.with_timescaledb_data || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">TimescaleDB verfügbar</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Mit NHITS</p>
        <p class="text-2xl font-bold text-primary-400">{{ symbolStats.with_nhits_model || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">Forecast-Modelle</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Favoriten</p>
        <p class="text-2xl font-bold text-yellow-400">{{ symbolStats.favorites_count || 0 }}</p>
        <p class="text-sm text-gray-500 mt-1">Watchlist</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Kategorien</p>
        <div class="flex flex-wrap gap-1 mt-1">
          <span v-for="(count, cat) in symbolStats.by_category" :key="cat"
            class="text-xs px-2 py-0.5 rounded" :class="getCategoryBadgeClass(cat)">
            {{ cat }}: {{ count }}
          </span>
        </div>
      </div>
    </div>

    <!-- Favorites Watchlist -->
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-3">
          <h3 class="text-lg font-semibold text-white">Favoriten Watchlist</h3>
          <span class="badge badge-primary">{{ favoriteSymbols.length }} Symbole</span>
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
              <th class="text-center py-3 px-2">Daten</th>
              <th class="text-center py-3 px-2">NHITS</th>
              <th class="text-right py-3 px-2">Datenpunkte</th>
              <th class="text-right py-3 px-2">Letzte Aktualisierung</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="sym in favoriteSymbols"
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
                <span v-if="sym.has_timescaledb_data" class="text-green-400">✓</span>
                <span v-else class="text-gray-500">-</span>
              </td>
              <td class="py-3 px-2 text-center">
                <span v-if="sym.has_nhits_model" class="text-green-400">✓</span>
                <span v-else class="text-gray-500">-</span>
              </td>
              <td class="py-3 px-2 text-right text-gray-300 font-mono">
                {{ sym.total_records?.toLocaleString() || '-' }}
              </td>
              <td class="py-3 px-2 text-right text-gray-400 text-sm">
                {{ formatTimestamp(sym.last_data_timestamp) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Quick Analysis Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Quick Analysis -->
      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-4">Schnellanalyse</h3>
        <div class="space-y-3">
          <div>
            <label class="text-sm text-gray-400 block mb-1">Symbol auswählen</label>
            <select v-model="selectedSymbol" class="select">
              <option v-for="s in kiSymbols" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <button
            @click="getQuickRecommendation"
            :disabled="isLoading"
            class="btn btn-primary w-full"
          >
            {{ isLoading ? 'Laden...' : 'Empfehlung abrufen' }}
          </button>
        </div>

        <!-- Recommendation Result -->
        <div v-if="recommendation" class="mt-4 p-3 bg-dark-300 rounded-lg">
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-400">Richtung</span>
            <span
              class="badge"
              :class="{
                'badge-success': recommendation.direction === 'LONG',
                'badge-danger': recommendation.direction === 'SHORT',
                'badge-warning': recommendation.direction === 'NEUTRAL'
              }"
            >
              {{ recommendation.direction }}
            </span>
          </div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-400">Konfidenz</span>
            <span class="text-white font-semibold">{{ recommendation.confidence_score }}%</span>
          </div>
          <div v-if="recommendation.entry_price" class="flex items-center justify-between mb-2">
            <span class="text-gray-400">Einstieg</span>
            <span class="text-white font-mono">{{ formatPrice(recommendation.entry_price) }}</span>
          </div>
          <div v-if="recommendation.stop_loss" class="flex items-center justify-between mb-2">
            <span class="text-gray-400">Stop Loss</span>
            <span class="text-red-400 font-mono">{{ formatPrice(recommendation.stop_loss) }}</span>
          </div>
          <div v-if="recommendation.take_profit_1" class="flex items-center justify-between">
            <span class="text-gray-400">Take Profit</span>
            <span class="text-green-400 font-mono">{{ formatPrice(recommendation.take_profit_1) }}</span>
          </div>
        </div>
      </div>

      <!-- Category Distribution -->
      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-4">Kategorien Übersicht</h3>
        <div class="space-y-3">
          <div v-for="(count, cat) in symbolStats.by_category" :key="cat"
            class="flex items-center justify-between p-2 bg-dark-300 rounded-lg">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full" :class="getCategoryDotClass(cat)"></span>
              <span class="text-white capitalize">{{ cat }}</span>
            </div>
            <span class="text-gray-300 font-mono">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- System Info -->
      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-4">System Info</h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between p-2 bg-dark-300 rounded-lg">
            <span class="text-gray-400">Aktive Symbole</span>
            <span class="text-green-400 font-semibold">{{ symbolStats.active_symbols || 0 }}</span>
          </div>
          <div class="flex items-center justify-between p-2 bg-dark-300 rounded-lg">
            <span class="text-gray-400">Inaktive Symbole</span>
            <span class="text-gray-500 font-semibold">{{ symbolStats.inactive_symbols || 0 }}</span>
          </div>
          <div class="flex items-center justify-between p-2 bg-dark-300 rounded-lg">
            <span class="text-gray-400">Suspendiert</span>
            <span class="text-red-400 font-semibold">{{ symbolStats.suspended_symbols || 0 }}</span>
          </div>
          <div class="flex items-center justify-between p-2 bg-dark-300 rounded-lg">
            <span class="text-gray-400">KI Modelle bereit</span>
            <span class="text-primary-400 font-semibold">{{ symbolStats.with_nhits_model || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- News Section -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Latest News</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <a
          v-for="article in news.slice(0, 6)"
          :key="article.url"
          :href="article.url"
          target="_blank"
          class="block p-4 bg-dark-300 rounded-lg hover:bg-dark-200 transition-colors"
        >
          <div class="flex items-center gap-2 mb-2">
            <span
              class="badge"
              :class="{
                'badge-success': article.sentiment === 'positive',
                'badge-danger': article.sentiment === 'negative',
                'badge-info': article.sentiment === 'neutral'
              }"
            >
              {{ article.sentiment || 'neutral' }}
            </span>
            <span class="text-xs text-gray-500">{{ article.source }}</span>
          </div>
          <h4 class="text-white font-medium line-clamp-2">{{ article.title }}</h4>
          <p class="text-gray-400 text-sm mt-2 line-clamp-2">{{ article.description }}</p>
          <p class="text-xs text-gray-500 mt-2">{{ formatDate(article.published_at) }}</p>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()
const router = useRouter()

const selectedSymbol = ref('BTCUSDT')
const recommendation = ref(null)

const news = computed(() => store.news)
const kiSymbols = computed(() => store.kiSymbols)
const isLoading = computed(() => store.isLoading)
const favoriteSymbols = computed(() => store.favoriteSymbols)
const symbolStats = computed(() => store.symbolStats || {})

async function getQuickRecommendation() {
  try {
    recommendation.value = await store.fetchRecommendation(selectedSymbol.value, false)
  } catch (e) {
    console.error('Failed to get recommendation:', e)
  }
}

async function refreshWatchlist() {
  await store.fetchFavoriteSymbols()
  await store.fetchSymbolStats()
}

function selectFavoriteSymbol(sym) {
  selectedSymbol.value = sym.symbol
  // Navigate to analysis page with selected symbol
  store.setSelectedSymbol(sym.symbol)
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

function getCategoryDotClass(category) {
  const classes = {
    crypto: 'bg-orange-500',
    forex: 'bg-blue-500',
    index: 'bg-purple-500',
    commodity: 'bg-yellow-500',
    stock: 'bg-green-500',
    etf: 'bg-cyan-500',
    other: 'bg-gray-500',
  }
  return classes[category] || classes.other
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

function formatPrice(value) {
  if (!value) return '$0'
  if (value < 0.01) return `$${value.toFixed(6)}`
  if (value < 1) return `$${value.toFixed(4)}`
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  if (store.kiSymbols.length > 0) {
    selectedSymbol.value = store.kiSymbols[0]
  }
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
