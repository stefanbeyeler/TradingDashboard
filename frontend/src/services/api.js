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

export default api
