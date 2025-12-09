import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Health & System
export const getHealth = () => api.get('/health')
export const getDashboard = (watchlist = 'BTC,ETH,SOL,XRP') =>
  api.get('/dashboard', { params: { watchlist } })

// KI Trading Model
export const getKISymbols = () => api.get('/ki/symbols')
export const getKIRecommendation = (symbol, useLlm = false, strategyId = null) =>
  api.get(`/ki/recommendation/${symbol}`, {
    params: { use_llm: useLlm, strategy_id: strategyId },
  })
export const analyzeSymbol = (data) => api.post('/ki/analyze', data)
export const getKIForecast = (symbol, horizon = 24) =>
  api.get(`/ki/forecast/${symbol}`, { params: { horizon } })
export const getKIStrategies = () => api.get('/ki/strategies')
export const getForecastModels = () => api.get('/ki/forecast-models')
export const queryRAG = (query, symbol = null, nResults = 5) =>
  api.get('/ki/rag/query', { params: { query, symbol, n_results: nResults } })
export const getQueryLogs = (limit = 50, offset = 0, symbol = null) =>
  api.get('/ki/query-logs', { params: { limit, offset, symbol } })
export const getLiveMarketData = (symbol) =>
  api.get(`/ki/market-data/${symbol}`)

// Crypto Markets
export const getCryptoMarkets = (perPage = 50, page = 1) =>
  api.get('/crypto/markets', { params: { per_page: perPage, page } })
export const getTrendingCrypto = () => api.get('/crypto/trending')
export const getGlobalCryptoData = () => api.get('/crypto/global')
export const getCryptoOHLC = (coinId, days = 30) =>
  api.get(`/crypto/${coinId}/ohlc`, { params: { days } })
export const getCryptoChart = (coinId, days = 30) =>
  api.get(`/crypto/${coinId}/chart`, { params: { days } })
export const searchCrypto = (query) =>
  api.get('/crypto/search', { params: { query } })

// Binance
export const getBinanceTickers = (symbol = null) =>
  api.get('/binance/ticker', { params: { symbol } })
export const getBinanceKlines = (symbol, interval = '1h', limit = 100) =>
  api.get(`/binance/klines/${symbol}`, { params: { interval, limit } })
export const getBinanceOrderbook = (symbol, limit = 20) =>
  api.get(`/binance/orderbook/${symbol}`, { params: { limit } })
export const getBinanceTrades = (symbol, limit = 50) =>
  api.get(`/binance/trades/${symbol}`, { params: { limit } })

// Stocks & Forex
export const getStockQuote = (symbol) => api.get(`/stocks/quote/${symbol}`)
export const getStockDaily = (symbol, outputsize = 'compact') =>
  api.get(`/stocks/daily/${symbol}`, { params: { outputsize } })
export const searchStocks = (keywords) =>
  api.get('/stocks/search', { params: { keywords } })
export const getForexRate = (fromCurrency, toCurrency = 'USD') =>
  api.get('/forex/rate', { params: { from_currency: fromCurrency, to_currency: toCurrency } })
export const getForexDaily = (fromSymbol, toSymbol = 'USD', outputsize = 'compact') =>
  api.get('/forex/daily', { params: { from_symbol: fromSymbol, to_symbol: toSymbol, outputsize } })
export const getRSI = (symbol, interval = 'daily', timePeriod = 14) =>
  api.get(`/indicators/rsi/${symbol}`, { params: { interval, time_period: timePeriod } })
export const getMACD = (symbol, interval = 'daily') =>
  api.get(`/indicators/macd/${symbol}`, { params: { interval } })

// News
export const getCryptoNews = (limit = 20) =>
  api.get('/news/crypto', { params: { limit } })
export const getMarketNews = (query = 'stock market trading', limit = 20) =>
  api.get('/news/market', { params: { query, limit } })
export const getCombinedNews = (limit = 30) =>
  api.get('/news/combined', { params: { limit } })

// Symbol Management
export const getManagedSymbols = (params = {}) =>
  api.get('/symbols', { params })
export const getSymbolStats = () => api.get('/symbols/stats')
export const searchSymbols = (query, limit = 20) =>
  api.get('/symbols/search', { params: { query, limit } })
export const importSymbols = () => api.post('/symbols/import')
export const createSymbol = (data) => api.post('/symbols', data)
export const getSymbol = (symbolId) => api.get(`/symbols/${symbolId}`)
export const updateSymbol = (symbolId, data) => api.put(`/symbols/${symbolId}`, data)
export const deleteSymbol = (symbolId) => api.delete(`/symbols/${symbolId}`)
export const toggleSymbolFavorite = (symbolId) => api.post(`/symbols/${symbolId}/favorite`)
export const refreshSymbol = (symbolId) => api.post(`/symbols/${symbolId}/refresh`)

// Trading Analyses (stored in DB)
export const getRecentAnalyses = (limit = 20, symbol = null) =>
  api.get('/analyses', { params: { limit, symbol } })
export const getAnalysis = (analysisId) => api.get(`/analyses/${analysisId}`)

// Backup/Restore
export const createBackup = () => api.get('/backup')
export const restoreBackup = (backupData, options = {}) =>
  api.post('/restore', {
    backup: backupData,
    restore_config: options.restoreConfig ?? true,
    restore_preferences: options.restorePreferences ?? true,
    restore_watchlists: options.restoreWatchlists ?? true,
    restore_alerts: options.restoreAlerts ?? true,
    restore_analyses: options.restoreAnalyses ?? true,
    restore_journal: options.restoreJournal ?? true,
    clear_existing: options.clearExisting ?? false,
  })

// Scheduled Analyses (Favorite Symbol Quick Analyses)
export const getScheduledAnalyses = () => api.get('/scheduled-analyses')
export const getScheduledAnalysisForSymbol = (symbol) => api.get(`/scheduled-analyses/${symbol}`)
export const runScheduledAnalyses = () => api.post('/scheduled-analyses/run')
export const getSchedulerStatus = () => api.get('/scheduler/status')
export const startScheduler = () => api.post('/scheduler/start')
export const stopScheduler = () => api.post('/scheduler/stop')
export const setSchedulerInterval = (intervalMinutes) =>
  api.put('/scheduler/interval', null, { params: { interval_minutes: intervalMinutes } })

export default api
