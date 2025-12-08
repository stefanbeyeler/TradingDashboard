import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/services/api'

export const useMarketStore = defineStore('market', () => {
  // State
  const watchlist = ref([])
  const globalData = ref(null)
  const trending = ref([])
  const news = ref([])
  const systemStatus = ref({})
  const isLoading = ref(false)
  const error = ref(null)

  // KI Trading Model state
  const kiSymbols = ref([])
  const kiStrategies = ref([])
  const forecastModels = ref([])
  const currentRecommendation = ref(null)
  const currentForecast = ref(null)

  // Favorite symbols from managed symbols
  const favoriteSymbols = ref([])

  // Symbol statistics
  const symbolStats = ref({})

  // Selected symbol
  const selectedSymbol = ref('BTCUSDT')

  // Scheduled analyses for favorites
  const scheduledAnalyses = ref([])
  const schedulerStatus = ref({})

  // Getters - Category neutral
  const watchlistByChange = computed(() =>
    [...watchlist.value].sort((a, b) => (b.change_percent_24h || 0) - (a.change_percent_24h || 0))
  )

  // Actions
  async function fetchDashboard(symbols = null) {
    isLoading.value = true
    error.value = null
    try {
      // If no symbols provided, try to use favorites first
      let watchlistSymbols = symbols
      if (!watchlistSymbols && favoriteSymbols.value.length > 0) {
        // Extract crypto symbols from favorites (e.g., BTCUSD -> BTC)
        watchlistSymbols = favoriteSymbols.value
          .filter(s => s.category === 'crypto')
          .map(s => s.symbol.replace(/USD$/, ''))
          .join(',')
      }
      if (!watchlistSymbols) {
        watchlistSymbols = 'BTC,ETH,SOL,XRP,BNB,ADA,DOGE,AVAX'
      }

      const data = await api.getDashboard(watchlistSymbols)
      watchlist.value = data.watchlist || []
      news.value = data.market_news || []
      systemStatus.value = data.system_status || {}
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch dashboard:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchFavoriteSymbols() {
    try {
      const response = await api.getManagedSymbols({ favorites_only: true })
      favoriteSymbols.value = response.data || response || []
    } catch (e) {
      console.error('Failed to fetch favorite symbols:', e)
    }
  }

  async function fetchSymbolStats() {
    try {
      const response = await api.getSymbolStats()
      symbolStats.value = response.data || response || {}
    } catch (e) {
      console.error('Failed to fetch symbol stats:', e)
    }
  }

  async function fetchMarkets(perPage = 50) {
    try {
      watchlist.value = await api.getCryptoMarkets(perPage)
    } catch (e) {
      console.error('Failed to fetch markets:', e)
    }
  }

  async function fetchGlobalData() {
    try {
      globalData.value = await api.getGlobalCryptoData()
    } catch (e) {
      console.error('Failed to fetch global data:', e)
    }
  }

  async function fetchTrending() {
    try {
      trending.value = await api.getTrendingCrypto()
    } catch (e) {
      console.error('Failed to fetch trending:', e)
    }
  }

  async function fetchNews(limit = 20) {
    try {
      news.value = await api.getCryptoNews(limit)
    } catch (e) {
      console.error('Failed to fetch news:', e)
    }
  }

  // KI Trading Model actions
  async function fetchKISymbols() {
    try {
      const data = await api.getKISymbols()
      kiSymbols.value = data.symbols || []
    } catch (e) {
      console.error('Failed to fetch KI symbols:', e)
    }
  }

  async function fetchKIStrategies() {
    try {
      kiStrategies.value = await api.getKIStrategies()
    } catch (e) {
      console.error('Failed to fetch KI strategies:', e)
    }
  }

  async function fetchForecastModels() {
    try {
      forecastModels.value = await api.getForecastModels()
    } catch (e) {
      console.error('Failed to fetch forecast models:', e)
    }
  }

  async function fetchRecommendation(symbol, useLlm = false, strategyId = null) {
    isLoading.value = true
    try {
      currentRecommendation.value = await api.getKIRecommendation(symbol, useLlm, strategyId)
      return currentRecommendation.value
    } catch (e) {
      console.error('Failed to fetch recommendation:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchForecast(symbol, horizon = 24) {
    isLoading.value = true
    try {
      currentForecast.value = await api.getKIForecast(symbol, horizon)
      return currentForecast.value
    } catch (e) {
      console.error('Failed to fetch forecast:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function analyzeSymbol(request) {
    isLoading.value = true
    try {
      return await api.analyzeSymbol(request)
    } catch (e) {
      console.error('Failed to analyze:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function setSelectedSymbol(symbol) {
    selectedSymbol.value = symbol
  }

  // Scheduled analyses actions
  async function fetchScheduledAnalyses() {
    try {
      const response = await api.getScheduledAnalyses()
      scheduledAnalyses.value = response.analyses || []
      schedulerStatus.value = response.status || {}
      return response
    } catch (e) {
      console.error('Failed to fetch scheduled analyses:', e)
      return { analyses: [], status: {} }
    }
  }

  async function runScheduledAnalysesNow() {
    isLoading.value = true
    try {
      const response = await api.runScheduledAnalyses()
      scheduledAnalyses.value = response.analyses || []
      return response
    } catch (e) {
      console.error('Failed to run scheduled analyses:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchSchedulerStatus() {
    try {
      schedulerStatus.value = await api.getSchedulerStatus()
      return schedulerStatus.value
    } catch (e) {
      console.error('Failed to fetch scheduler status:', e)
      return {}
    }
  }

  return {
    // State
    watchlist,
    globalData,
    trending,
    news,
    systemStatus,
    isLoading,
    error,
    kiSymbols,
    kiStrategies,
    forecastModels,
    currentRecommendation,
    currentForecast,
    selectedSymbol,
    favoriteSymbols,
    symbolStats,
    scheduledAnalyses,
    schedulerStatus,

    // Getters
    watchlistByChange,

    // Actions
    fetchDashboard,
    fetchFavoriteSymbols,
    fetchSymbolStats,
    fetchMarkets,
    fetchGlobalData,
    fetchTrending,
    fetchNews,
    fetchKISymbols,
    fetchKIStrategies,
    fetchForecastModels,
    fetchRecommendation,
    fetchForecast,
    analyzeSymbol,
    setSelectedSymbol,
    fetchScheduledAnalyses,
    runScheduledAnalysesNow,
    fetchSchedulerStatus,
  }
})
