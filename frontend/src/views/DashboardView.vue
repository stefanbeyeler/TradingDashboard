<template>
  <div class="space-y-6">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Total Market Cap</p>
        <p class="text-2xl font-bold text-white">{{ formatCurrency(totalMarketCap) }}</p>
        <p class="text-sm text-gray-500 mt-1">Global crypto market</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">24h Volume</p>
        <p class="text-2xl font-bold text-white">{{ formatCurrency(totalVolume) }}</p>
        <p class="text-sm text-gray-500 mt-1">Trading volume</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">BTC Dominance</p>
        <p class="text-2xl font-bold text-primary-400">{{ btcDominance }}%</p>
        <p class="text-sm text-gray-500 mt-1">Market share</p>
      </div>
      <div class="card">
        <p class="text-sm text-gray-400 mb-1">Active Coins</p>
        <p class="text-2xl font-bold text-white">{{ activeCryptos }}</p>
        <p class="text-sm text-gray-500 mt-1">Tracked currencies</p>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Watchlist -->
      <div class="lg:col-span-2 card">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-white">Watchlist</h3>
          <button @click="refreshWatchlist" class="btn btn-secondary text-sm">
            Refresh
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-gray-400 text-sm border-b border-gray-700">
                <th class="text-left py-3 px-2">#</th>
                <th class="text-left py-3 px-2">Asset</th>
                <th class="text-right py-3 px-2">Price</th>
                <th class="text-right py-3 px-2">24h %</th>
                <th class="text-right py-3 px-2">Volume</th>
                <th class="text-right py-3 px-2">Market Cap</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(coin, index) in watchlist"
                :key="coin.symbol"
                class="border-b border-gray-700/50 hover:bg-dark-300/50 cursor-pointer transition-colors"
                @click="selectCoin(coin)"
              >
                <td class="py-3 px-2 text-gray-400">{{ index + 1 }}</td>
                <td class="py-3 px-2">
                  <div class="flex items-center gap-2">
                    <span class="font-semibold text-white">{{ coin.symbol }}</span>
                    <span class="text-gray-400 text-sm">{{ coin.name }}</span>
                  </div>
                </td>
                <td class="py-3 px-2 text-right font-mono text-white">
                  {{ formatPrice(coin.price) }}
                </td>
                <td
                  class="py-3 px-2 text-right font-mono"
                  :class="coin.change_percent_24h >= 0 ? 'text-green-400' : 'text-red-400'"
                >
                  {{ formatPercent(coin.change_percent_24h) }}
                </td>
                <td class="py-3 px-2 text-right text-gray-300">
                  {{ formatCurrency(coin.volume_24h) }}
                </td>
                <td class="py-3 px-2 text-right text-gray-300">
                  {{ formatCurrency(coin.market_cap) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Quick Analysis -->
        <div class="card">
          <h3 class="text-lg font-semibold text-white mb-4">Quick Analysis</h3>
          <div class="space-y-3">
            <div>
              <label class="text-sm text-gray-400 block mb-1">Symbol</label>
              <select v-model="selectedSymbol" class="select">
                <option v-for="s in kiSymbols" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <button
              @click="getQuickRecommendation"
              :disabled="isLoading"
              class="btn btn-primary w-full"
            >
              {{ isLoading ? 'Loading...' : 'Get Recommendation' }}
            </button>
          </div>

          <!-- Recommendation Result -->
          <div v-if="recommendation" class="mt-4 p-3 bg-dark-300 rounded-lg">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-400">Direction</span>
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
              <span class="text-gray-400">Confidence</span>
              <span class="text-white font-semibold">{{ recommendation.confidence_score }}%</span>
            </div>
            <div v-if="recommendation.entry_price" class="flex items-center justify-between mb-2">
              <span class="text-gray-400">Entry</span>
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

        <!-- Top Gainers/Losers -->
        <div class="card">
          <h3 class="text-lg font-semibold text-white mb-4">Top Movers</h3>
          <div class="space-y-2">
            <p class="text-sm text-gray-400">Gainers</p>
            <div v-for="coin in topGainers" :key="coin.symbol" class="flex justify-between items-center py-1">
              <span class="text-white">{{ coin.symbol }}</span>
              <span class="text-green-400 font-mono">+{{ formatPercent(coin.change_percent_24h) }}</span>
            </div>
            <p class="text-sm text-gray-400 mt-3">Losers</p>
            <div v-for="coin in topLosers" :key="coin.symbol" class="flex justify-between items-center py-1">
              <span class="text-white">{{ coin.symbol }}</span>
              <span class="text-red-400 font-mono">{{ formatPercent(coin.change_percent_24h) }}</span>
            </div>
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
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()

const selectedSymbol = ref('BTCUSDT')
const recommendation = ref(null)

const watchlist = computed(() => store.watchlist)
const news = computed(() => store.news)
const kiSymbols = computed(() => store.kiSymbols)
const isLoading = computed(() => store.isLoading)
const topGainers = computed(() => store.topGainers)
const topLosers = computed(() => store.topLosers)
const totalMarketCap = computed(() => store.globalData?.total_market_cap?.usd || 0)
const totalVolume = computed(() => store.globalData?.total_volume?.usd || 0)
const btcDominance = computed(() => store.btcDominance?.toFixed(1) || '0')
const activeCryptos = computed(() => store.globalData?.active_cryptocurrencies || 0)

async function getQuickRecommendation() {
  try {
    recommendation.value = await store.fetchRecommendation(selectedSymbol.value, false)
  } catch (e) {
    console.error('Failed to get recommendation:', e)
  }
}

async function refreshWatchlist() {
  await store.fetchDashboard()
}

function selectCoin(coin) {
  selectedSymbol.value = coin.symbol + 'USDT'
}

function formatCurrency(value) {
  if (!value) return '$0'
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
  return `$${value.toLocaleString()}`
}

function formatPrice(value) {
  if (!value) return '$0'
  if (value < 0.01) return `$${value.toFixed(6)}`
  if (value < 1) return `$${value.toFixed(4)}`
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatPercent(value) {
  if (!value) return '0.00%'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
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
