<template>
  <div class="space-y-6">
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

    <!-- Quick Analysis -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Schnellanalyse</h3>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
        <div v-if="recommendation" class="p-4 bg-dark-300 rounded-lg">
          <div class="flex items-center justify-between mb-3">
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
          <div class="flex items-center justify-between mb-3">
            <span class="text-gray-400">Konfidenz</span>
            <span class="text-white font-semibold">{{ recommendation.confidence_score }}%</span>
          </div>
          <div v-if="recommendation.entry_price" class="flex items-center justify-between mb-3">
            <span class="text-gray-400">Einstieg</span>
            <span class="text-white font-mono">{{ formatPrice(recommendation.entry_price) }}</span>
          </div>
          <div v-if="recommendation.stop_loss" class="flex items-center justify-between mb-3">
            <span class="text-gray-400">Stop Loss</span>
            <span class="text-red-400 font-mono">{{ formatPrice(recommendation.stop_loss) }}</span>
          </div>
          <div v-if="recommendation.take_profit_1" class="flex items-center justify-between">
            <span class="text-gray-400">Take Profit</span>
            <span class="text-green-400 font-mono">{{ formatPrice(recommendation.take_profit_1) }}</span>
          </div>
        </div>
        <div v-else class="p-4 bg-dark-300 rounded-lg flex items-center justify-center text-gray-500">
          Wählen Sie ein Symbol und klicken Sie auf "Empfehlung abrufen"
        </div>
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

const kiSymbols = computed(() => store.kiSymbols)
const isLoading = computed(() => store.isLoading)
const favoriteSymbols = computed(() => store.favoriteSymbols)

async function getQuickRecommendation() {
  try {
    recommendation.value = await store.fetchRecommendation(selectedSymbol.value, false)
  } catch (e) {
    console.error('Failed to get recommendation:', e)
  }
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

onMounted(async () => {
  if (store.kiSymbols.length > 0) {
    selectedSymbol.value = store.kiSymbols[0]
  }
})
</script>
