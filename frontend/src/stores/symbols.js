import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/services/api'

export const useSymbolStore = defineStore('symbols', () => {
  // State
  const symbols = ref([])
  const stats = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Filters
  const searchQuery = ref('')
  const categoryFilter = ref('')
  const statusFilter = ref('')
  const favoritesOnly = ref(false)
  const withDataOnly = ref(false)

  // Getters
  const filteredSymbols = computed(() => {
    let result = [...symbols.value]

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(
        (s) =>
          s.symbol.toLowerCase().includes(query) ||
          (s.display_name && s.display_name.toLowerCase().includes(query))
      )
    }

    if (categoryFilter.value) {
      result = result.filter((s) => s.category === categoryFilter.value)
    }

    if (statusFilter.value) {
      result = result.filter((s) => s.status === statusFilter.value)
    }

    if (favoritesOnly.value) {
      result = result.filter((s) => s.is_favorite)
    }

    if (withDataOnly.value) {
      result = result.filter((s) => s.has_timescaledb_data)
    }

    return result
  })

  const favoriteSymbols = computed(() => symbols.value.filter((s) => s.is_favorite))

  const symbolsWithData = computed(() => symbols.value.filter((s) => s.has_timescaledb_data))

  const symbolsWithModel = computed(() => symbols.value.filter((s) => s.has_nhits_model))

  // Actions
  async function fetchSymbols(params = {}) {
    isLoading.value = true
    error.value = null
    try {
      symbols.value = await api.getManagedSymbols(params)
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch symbols:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStats() {
    try {
      stats.value = await api.getSymbolStats()
    } catch (e) {
      console.error('Failed to fetch stats:', e)
    }
  }

  async function importFromTimescaleDB() {
    isLoading.value = true
    error.value = null
    try {
      const result = await api.importSymbols()
      await fetchSymbols()
      await fetchStats()
      return result
    } catch (e) {
      error.value = e.message
      console.error('Failed to import symbols:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function createSymbol(data) {
    isLoading.value = true
    try {
      const symbol = await api.createSymbol(data)
      symbols.value.push(symbol)
      await fetchStats()
      return symbol
    } catch (e) {
      console.error('Failed to create symbol:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function updateSymbol(symbolId, data) {
    isLoading.value = true
    try {
      const updated = await api.updateSymbol(symbolId, data)
      const index = symbols.value.findIndex((s) => s.symbol === symbolId)
      if (index >= 0) {
        symbols.value[index] = updated
      }
      return updated
    } catch (e) {
      console.error('Failed to update symbol:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function deleteSymbol(symbolId) {
    isLoading.value = true
    try {
      await api.deleteSymbol(symbolId)
      symbols.value = symbols.value.filter((s) => s.symbol !== symbolId)
      await fetchStats()
    } catch (e) {
      console.error('Failed to delete symbol:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function toggleFavorite(symbolId) {
    try {
      const updated = await api.toggleSymbolFavorite(symbolId)
      const index = symbols.value.findIndex((s) => s.symbol === symbolId)
      if (index >= 0) {
        symbols.value[index] = updated
      }
      await fetchStats()
      return updated
    } catch (e) {
      console.error('Failed to toggle favorite:', e)
      throw e
    }
  }

  async function refreshSymbol(symbolId) {
    try {
      const updated = await api.refreshSymbol(symbolId)
      const index = symbols.value.findIndex((s) => s.symbol === symbolId)
      if (index >= 0) {
        symbols.value[index] = updated
      }
      return updated
    } catch (e) {
      console.error('Failed to refresh symbol:', e)
      throw e
    }
  }

  async function searchSymbols(query, limit = 20) {
    try {
      return await api.searchSymbols(query, limit)
    } catch (e) {
      console.error('Failed to search symbols:', e)
      return { count: 0, symbols: [] }
    }
  }

  function setFilters({ search, category, status, favorites, withData }) {
    if (search !== undefined) searchQuery.value = search
    if (category !== undefined) categoryFilter.value = category
    if (status !== undefined) statusFilter.value = status
    if (favorites !== undefined) favoritesOnly.value = favorites
    if (withData !== undefined) withDataOnly.value = withData
  }

  function clearFilters() {
    searchQuery.value = ''
    categoryFilter.value = ''
    statusFilter.value = ''
    favoritesOnly.value = false
    withDataOnly.value = false
  }

  return {
    // State
    symbols,
    stats,
    isLoading,
    error,
    searchQuery,
    categoryFilter,
    statusFilter,
    favoritesOnly,
    withDataOnly,

    // Getters
    filteredSymbols,
    favoriteSymbols,
    symbolsWithData,
    symbolsWithModel,

    // Actions
    fetchSymbols,
    fetchStats,
    importFromTimescaleDB,
    createSymbol,
    updateSymbol,
    deleteSymbol,
    toggleFavorite,
    refreshSymbol,
    searchSymbols,
    setFilters,
    clearFilters,
  }
})
