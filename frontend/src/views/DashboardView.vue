<template>
  <div class="space-y-6">
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()
const router = useRouter()

const favoriteSymbols = computed(() => store.favoriteSymbols)

// Sort favorites by category and then by symbol name
const sortedFavoriteSymbols = computed(() => {
  return [...favoriteSymbols.value].sort((a, b) => {
    // First sort by category
    const categoryCompare = (a.category || '').localeCompare(b.category || '')
    if (categoryCompare !== 0) return categoryCompare
    // Then sort by symbol name
    return (a.symbol || '').localeCompare(b.symbol || '')
  })
})

function selectFavoriteSymbol(sym) {
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
</script>
