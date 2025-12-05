<template>
  <div class="space-y-6">
    <!-- Search & Filters -->
    <div class="card">
      <div class="flex flex-wrap gap-4 items-center">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search markets..."
            class="input"
          />
        </div>
        <div class="flex gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="btn"
            :class="activeTab === tab.id ? 'btn-primary' : 'btn-secondary'"
          >
            {{ tab.name }}
          </button>
        </div>
        <button @click="refreshData" :disabled="loading" class="btn btn-secondary">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- Crypto Markets -->
    <div v-if="activeTab === 'crypto'" class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Cryptocurrency Markets</h3>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-gray-700">
              <th class="text-left py-3 px-2">#</th>
              <th class="text-left py-3 px-2 cursor-pointer hover:text-white" @click="sortBy('symbol')">
                Asset {{ sortField === 'symbol' ? (sortAsc ? '↑' : '↓') : '' }}
              </th>
              <th class="text-right py-3 px-2 cursor-pointer hover:text-white" @click="sortBy('price')">
                Price {{ sortField === 'price' ? (sortAsc ? '↑' : '↓') : '' }}
              </th>
              <th class="text-right py-3 px-2 cursor-pointer hover:text-white" @click="sortBy('change_percent_24h')">
                24h % {{ sortField === 'change_percent_24h' ? (sortAsc ? '↑' : '↓') : '' }}
              </th>
              <th class="text-right py-3 px-2 cursor-pointer hover:text-white" @click="sortBy('volume_24h')">
                Volume {{ sortField === 'volume_24h' ? (sortAsc ? '↑' : '↓') : '' }}
              </th>
              <th class="text-right py-3 px-2 cursor-pointer hover:text-white" @click="sortBy('market_cap')">
                Market Cap {{ sortField === 'market_cap' ? (sortAsc ? '↑' : '↓') : '' }}
              </th>
              <th class="text-center py-3 px-2">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(coin, index) in filteredCryptos"
              :key="coin.symbol"
              class="border-b border-gray-700/50 hover:bg-dark-300/50 transition-colors"
            >
              <td class="py-3 px-2 text-gray-400">{{ index + 1 }}</td>
              <td class="py-3 px-2">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-white">{{ coin.symbol }}</span>
                  <span class="text-gray-400 text-sm hidden md:inline">{{ coin.name }}</span>
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
              <td class="py-3 px-2 text-center">
                <button
                  @click="analyzeSymbol(coin.symbol)"
                  class="text-primary-400 hover:text-primary-300 text-sm"
                >
                  Analyze
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex justify-between items-center mt-4">
        <span class="text-gray-400 text-sm">
          Showing {{ filteredCryptos.length }} of {{ cryptoMarkets.length }} assets
        </span>
        <div class="flex gap-2">
          <button
            @click="loadMore"
            :disabled="loading"
            class="btn btn-secondary text-sm"
          >
            Load More
          </button>
        </div>
      </div>
    </div>

    <!-- Binance Tickers -->
    <div v-if="activeTab === 'binance'" class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Binance Live Tickers</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="ticker in filteredBinance"
          :key="ticker.symbol"
          class="bg-dark-300 rounded-lg p-4 hover:bg-dark-200 transition-colors cursor-pointer"
          @click="showDetails(ticker)"
        >
          <div class="flex justify-between items-start mb-2">
            <span class="font-semibold text-white">{{ ticker.symbol }}</span>
            <span
              class="badge"
              :class="ticker.change_percent_24h >= 0 ? 'badge-success' : 'badge-danger'"
            >
              {{ formatPercent(ticker.change_percent_24h) }}
            </span>
          </div>
          <div class="text-2xl font-mono text-white mb-2">
            {{ formatPrice(ticker.price) }}
          </div>
          <div class="text-sm text-gray-400">
            Vol: {{ formatCurrency(ticker.volume_24h) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Forex Rates -->
    <div v-if="activeTab === 'forex'" class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Forex Exchange Rates</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="pair in forexPairs"
          :key="pair.from"
          class="bg-dark-300 rounded-lg p-4"
        >
          <div class="flex justify-between items-center mb-2">
            <span class="font-semibold text-white">{{ pair.from }}/{{ pair.to }}</span>
            <button
              @click="loadForexRate(pair.from, pair.to)"
              class="text-primary-400 hover:text-primary-300 text-sm"
            >
              Refresh
            </button>
          </div>
          <div v-if="forexRates[`${pair.from}/${pair.to}`]" class="text-2xl font-mono text-white">
            {{ formatPrice(forexRates[`${pair.from}/${pair.to}`].price) }}
          </div>
          <div v-else class="text-gray-500">Loading...</div>
        </div>
      </div>
    </div>

    <!-- Stock Search -->
    <div v-if="activeTab === 'stocks'" class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Stock Markets</h3>
      <div class="mb-4">
        <div class="flex gap-2">
          <input
            v-model="stockSearch"
            type="text"
            placeholder="Search stocks (e.g., AAPL, MSFT)..."
            class="input flex-1"
            @keyup.enter="searchStocks"
          />
          <button @click="searchStocks" class="btn btn-primary">
            Search
          </button>
        </div>
      </div>

      <!-- Stock Search Results -->
      <div v-if="stockResults.length" class="space-y-2">
        <div
          v-for="stock in stockResults"
          :key="stock.symbol"
          class="flex items-center justify-between p-3 bg-dark-300 rounded-lg hover:bg-dark-200 cursor-pointer"
          @click="loadStockQuote(stock.symbol)"
        >
          <div>
            <span class="font-semibold text-white">{{ stock.symbol }}</span>
            <span class="text-gray-400 text-sm ml-2">{{ stock.name }}</span>
          </div>
          <div class="text-sm text-gray-400">
            {{ stock.type }} - {{ stock.region }}
          </div>
        </div>
      </div>

      <!-- Selected Stock Quote -->
      <div v-if="selectedStock" class="mt-4 p-4 bg-dark-300 rounded-lg">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h4 class="text-xl font-semibold text-white">{{ selectedStock.symbol }}</h4>
            <p class="text-gray-400">{{ selectedStock.name }}</p>
          </div>
          <div class="text-right">
            <div class="text-2xl font-mono text-white">{{ formatPrice(selectedStock.price) }}</div>
            <div
              class="font-mono"
              :class="selectedStock.change_percent_24h >= 0 ? 'text-green-400' : 'text-red-400'"
            >
              {{ formatPercent(selectedStock.change_percent_24h) }}
            </div>
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-400">High</span>
            <p class="text-white font-mono">{{ formatPrice(selectedStock.high_24h) }}</p>
          </div>
          <div>
            <span class="text-gray-400">Low</span>
            <p class="text-white font-mono">{{ formatPrice(selectedStock.low_24h) }}</p>
          </div>
          <div>
            <span class="text-gray-400">Volume</span>
            <p class="text-white">{{ formatCurrency(selectedStock.volume_24h) }}</p>
          </div>
          <div>
            <span class="text-gray-400">Change</span>
            <p class="text-white font-mono">{{ formatPrice(selectedStock.change_24h) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as api from '@/services/api'
import { useMarketStore } from '@/stores/market'

const router = useRouter()
const store = useMarketStore()

const activeTab = ref('crypto')
const searchQuery = ref('')
const loading = ref(false)

// Crypto
const cryptoMarkets = ref([])
const currentPage = ref(1)

// Binance
const binanceTickers = ref([])

// Forex
const forexPairs = [
  { from: 'EUR', to: 'USD' },
  { from: 'GBP', to: 'USD' },
  { from: 'USD', to: 'JPY' },
  { from: 'USD', to: 'CHF' },
  { from: 'AUD', to: 'USD' },
  { from: 'USD', to: 'CAD' },
]
const forexRates = ref({})

// Stocks
const stockSearch = ref('')
const stockResults = ref([])
const selectedStock = ref(null)

// Sorting
const sortField = ref('market_cap')
const sortAsc = ref(false)

const tabs = [
  { id: 'crypto', name: 'Crypto' },
  { id: 'binance', name: 'Binance' },
  { id: 'forex', name: 'Forex' },
  { id: 'stocks', name: 'Stocks' },
]

// Computed
const filteredCryptos = computed(() => {
  let result = [...cryptoMarkets.value]

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(c =>
      c.symbol.toLowerCase().includes(query) ||
      c.name?.toLowerCase().includes(query)
    )
  }

  result.sort((a, b) => {
    const aVal = a[sortField.value] || 0
    const bVal = b[sortField.value] || 0
    return sortAsc.value ? aVal - bVal : bVal - aVal
  })

  return result
})

const filteredBinance = computed(() => {
  if (!searchQuery.value) return binanceTickers.value
  const query = searchQuery.value.toUpperCase()
  return binanceTickers.value.filter(t => t.symbol.includes(query))
})

// Methods
async function refreshData() {
  loading.value = true
  try {
    if (activeTab.value === 'crypto') {
      cryptoMarkets.value = await api.getCryptoMarkets(100)
    } else if (activeTab.value === 'binance') {
      binanceTickers.value = await api.getBinanceTickers()
    }
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  loading.value = true
  try {
    currentPage.value++
    const more = await api.getCryptoMarkets(50, currentPage.value)
    cryptoMarkets.value.push(...more)
  } finally {
    loading.value = false
  }
}

function sortBy(field) {
  if (sortField.value === field) {
    sortAsc.value = !sortAsc.value
  } else {
    sortField.value = field
    sortAsc.value = false
  }
}

async function loadForexRate(from, to) {
  try {
    const rate = await api.getForexRate(from, to)
    forexRates.value[`${from}/${to}`] = rate
  } catch (e) {
    console.error('Failed to load forex rate:', e)
  }
}

async function searchStocks() {
  if (!stockSearch.value) return
  try {
    stockResults.value = await api.searchStocks(stockSearch.value)
  } catch (e) {
    console.error('Failed to search stocks:', e)
  }
}

async function loadStockQuote(symbol) {
  try {
    selectedStock.value = await api.getStockQuote(symbol)
  } catch (e) {
    console.error('Failed to load stock quote:', e)
  }
}

function showDetails(ticker) {
  store.setSelectedSymbol(ticker.symbol)
}

function analyzeSymbol(symbol) {
  store.setSelectedSymbol(symbol + 'USDT')
  router.push('/analysis')
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

onMounted(async () => {
  await refreshData()

  // Load forex rates
  for (const pair of forexPairs) {
    loadForexRate(pair.from, pair.to)
  }
})
</script>
