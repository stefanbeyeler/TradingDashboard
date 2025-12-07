<template>
  <div class="space-y-6">
    <!-- Header & Stats -->
    <div class="card">
      <div class="flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-white">Symbol Management</h2>
          <p class="text-gray-400 text-sm mt-1">Manage trading symbols from TimescaleDB</p>
        </div>
        <div class="flex gap-2">
          <button @click="handleImport" :disabled="isLoading" class="btn btn-primary">
            {{ isLoading ? 'Importing...' : 'Import from TimescaleDB' }}
          </button>
          <button @click="showCreateModal = true" class="btn btn-secondary">
            + New Symbol
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div v-if="stats" class="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
        <div class="bg-dark-300 rounded-lg p-3">
          <div class="text-gray-400 text-xs">Total</div>
          <div class="text-white text-lg font-bold">{{ stats.total_symbols }}</div>
        </div>
        <div class="bg-dark-300 rounded-lg p-3">
          <div class="text-gray-400 text-xs">Active</div>
          <div class="text-green-400 text-lg font-bold">{{ stats.active_symbols }}</div>
        </div>
        <div class="bg-dark-300 rounded-lg p-3">
          <div class="text-gray-400 text-xs">With Data</div>
          <div class="text-blue-400 text-lg font-bold">{{ stats.with_timescaledb_data }}</div>
        </div>
        <div class="bg-dark-300 rounded-lg p-3">
          <div class="text-gray-400 text-xs">With Model</div>
          <div class="text-purple-400 text-lg font-bold">{{ stats.with_nhits_model }}</div>
        </div>
        <div class="bg-dark-300 rounded-lg p-3">
          <div class="text-gray-400 text-xs">Favorites</div>
          <div class="text-yellow-400 text-lg font-bold">{{ stats.favorites_count }}</div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="flex flex-wrap gap-4 items-center">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search symbols..."
            class="input"
            @input="handleSearch"
          />
        </div>
        <select v-model="categoryFilter" class="input w-auto" @change="handleCategoryFilterChange">
          <option value="">All Categories</option>
          <option value="forex">Forex</option>
          <option value="crypto">Crypto</option>
          <option value="stock">Stocks</option>
          <option value="index">Indices</option>
          <option value="commodity">Commodities</option>
          <option value="other">Other</option>
        </select>
        <select
          v-model="subcategoryFilter"
          class="input w-auto"
          :disabled="!categoryFilter || subcategoryOptions.length === 0"
          @change="handleFilterChange"
        >
          <option value="">All Subcategories</option>
          <option v-for="opt in subcategoryOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <select v-model="statusFilter" class="input w-auto" @change="handleFilterChange">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="suspended">Suspended</option>
        </select>
        <label class="flex items-center gap-2 text-gray-400 text-sm cursor-pointer">
          <input type="checkbox" v-model="favoritesOnly" @change="handleFilterChange" class="form-checkbox" />
          Favorites only
        </label>
        <label class="flex items-center gap-2 text-gray-400 text-sm cursor-pointer">
          <input type="checkbox" v-model="withDataOnly" @change="handleFilterChange" class="form-checkbox" />
          With data only
        </label>
        <button @click="loadSymbols" :disabled="isLoading" class="btn btn-secondary">
          {{ isLoading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- Symbols Table -->
    <div class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-gray-700">
              <th class="text-center py-3 px-2 w-12"></th>
              <th class="text-left py-3 px-2">Symbol</th>
              <th class="text-left py-3 px-2">Category</th>
              <th class="text-center py-3 px-2">Status</th>
              <th class="text-center py-3 px-2">Data</th>
              <th class="text-left py-3 px-2">Last Update</th>
              <th class="text-right py-3 px-2">Records</th>
              <th class="text-center py-3 px-2">NHITS</th>
              <th class="text-center py-3 px-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="symbol in filteredSymbols"
              :key="symbol.symbol"
              class="border-b border-gray-700/50 hover:bg-dark-300/50 transition-colors"
            >
              <td class="py-3 px-2 text-center">
                <button
                  @click="handleToggleFavorite(symbol.symbol)"
                  class="text-xl hover:scale-110 transition-transform"
                >
                  {{ symbol.is_favorite ? '⭐' : '☆' }}
                </button>
              </td>
              <td class="py-3 px-2">
                <div class="font-semibold text-white">{{ symbol.symbol }}</div>
                <div v-if="symbol.display_name && symbol.display_name !== symbol.symbol" class="text-gray-400 text-xs">
                  {{ symbol.display_name }}
                </div>
              </td>
              <td class="py-3 px-2">
                <div class="flex flex-col gap-1">
                  <span class="px-2 py-1 bg-dark-300 rounded text-xs text-gray-300">
                    {{ categoryLabels[symbol.category] || symbol.category }}
                  </span>
                  <span v-if="symbol.subcategory" class="px-2 py-0.5 bg-dark-400 rounded text-xs text-gray-400">
                    {{ subcategoryLabels[symbol.subcategory] || symbol.subcategory }}
                  </span>
                </div>
              </td>
              <td class="py-3 px-2 text-center">
                <span
                  class="inline-flex items-center gap-1"
                  :class="{
                    'text-green-400': symbol.status === 'active',
                    'text-yellow-400': symbol.status === 'inactive',
                    'text-red-400': symbol.status === 'suspended'
                  }"
                >
                  <span class="w-2 h-2 rounded-full" :class="{
                    'bg-green-400': symbol.status === 'active',
                    'bg-yellow-400': symbol.status === 'inactive',
                    'bg-red-400': symbol.status === 'suspended'
                  }"></span>
                  {{ statusLabels[symbol.status] || symbol.status }}
                </span>
              </td>
              <td class="py-3 px-2 text-center text-xl">
                {{ symbol.has_timescaledb_data ? '✅' : '❌' }}
              </td>
              <td class="py-3 px-2 text-gray-400 text-sm">
                {{ formatDate(symbol.last_data_timestamp) }}
              </td>
              <td class="py-3 px-2 text-right text-gray-300 font-mono">
                {{ formatNumber(symbol.total_records) }}
              </td>
              <td class="py-3 px-2 text-center text-xl">
                {{ symbol.has_nhits_model ? '✅' : '❌' }}
              </td>
              <td class="py-3 px-2">
                <div class="flex gap-1 justify-center">
                  <button
                    @click="editSymbol(symbol)"
                    class="px-2 py-1 bg-dark-300 hover:bg-dark-200 rounded text-xs text-gray-300"
                  >
                    Edit
                  </button>
                  <button
                    @click="handleRefresh(symbol.symbol)"
                    class="px-2 py-1 bg-dark-300 hover:bg-dark-200 rounded text-xs text-gray-300"
                    title="Refresh data"
                  >
                    ↻
                  </button>
                  <button
                    @click="handleDelete(symbol.symbol)"
                    class="px-2 py-1 bg-red-900/50 hover:bg-red-800 rounded text-xs text-red-300"
                  >
                    ✕
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredSymbols.length === 0">
              <td colspan="9" class="py-8 text-center text-gray-400">
                {{ isLoading ? 'Loading symbols...' : 'No symbols found. Click "Import from TimescaleDB" to get started.' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || showEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="closeModal">
      <div class="bg-dark-200 rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-bold text-white mb-4">
          {{ showEditModal ? `Edit Symbol: ${editingSymbol?.symbol}` : 'Create New Symbol' }}
        </h3>
        <form @submit.prevent="handleSaveSymbol" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-400 text-sm mb-1">Symbol *</label>
              <input
                v-model="formData.symbol"
                type="text"
                class="input"
                required
                :disabled="showEditModal"
                placeholder="e.g. EURUSD"
              />
            </div>
            <div>
              <label class="block text-gray-400 text-sm mb-1">Display Name</label>
              <input
                v-model="formData.display_name"
                type="text"
                class="input"
                placeholder="e.g. Euro/US Dollar"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-400 text-sm mb-1">Category</label>
              <select v-model="formData.category" class="input" @change="onCategoryChange">
                <option value="forex">Forex</option>
                <option value="crypto">Crypto</option>
                <option value="stock">Stocks</option>
                <option value="index">Indices</option>
                <option value="commodity">Commodities</option>
                <option value="etf">ETF</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-400 text-sm mb-1">Subcategory</label>
              <select v-model="formData.subcategory" class="input">
                <option value="">-- None --</option>
                <optgroup v-if="formData.category === 'forex'" label="Forex">
                  <option value="major">Major</option>
                  <option value="minor">Minor</option>
                  <option value="exotic">Exotic</option>
                </optgroup>
                <optgroup v-if="formData.category === 'crypto'" label="Crypto">
                  <option value="large_cap">Large Cap</option>
                  <option value="mid_cap">Mid Cap</option>
                  <option value="small_cap">Small Cap</option>
                  <option value="defi">DeFi</option>
                  <option value="meme">Meme</option>
                  <option value="stablecoin">Stablecoin</option>
                </optgroup>
                <optgroup v-if="formData.category === 'stock'" label="Stocks">
                  <option value="tech">Tech</option>
                  <option value="finance">Finance</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="energy">Energy</option>
                  <option value="consumer">Consumer</option>
                  <option value="industrial">Industrial</option>
                </optgroup>
                <optgroup v-if="formData.category === 'index'" label="Indices">
                  <option value="global">Global</option>
                  <option value="regional">Regional</option>
                  <option value="sector">Sector</option>
                </optgroup>
                <optgroup v-if="formData.category === 'commodity'" label="Commodities">
                  <option value="precious_metal">Precious Metal</option>
                  <option value="base_metal">Base Metal</option>
                  <option value="agriculture">Agriculture</option>
                  <option value="energy_commodity">Energy</option>
                </optgroup>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-400 text-sm mb-1">Status</label>
              <select v-model="formData.status" class="input">
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
            <div>
              <label class="block text-gray-400 text-sm mb-1">Base Currency</label>
              <input v-model="formData.base_currency" type="text" class="input" placeholder="e.g. EUR" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-gray-400 text-sm mb-1">Quote Currency</label>
              <input v-model="formData.quote_currency" type="text" class="input" placeholder="e.g. USD" />
            </div>
            <div class="flex items-end">
              <label class="flex items-center gap-2 text-gray-300 text-sm cursor-pointer pb-2">
                <input type="checkbox" v-model="formData.is_favorite" class="form-checkbox" />
                Mark as favorite
              </label>
            </div>
          </div>
          <div>
            <label class="block text-gray-400 text-sm mb-1">Description</label>
            <textarea v-model="formData.description" class="input" rows="2" placeholder="Symbol description..."></textarea>
          </div>
          <div>
            <label class="block text-gray-400 text-sm mb-1">Notes</label>
            <textarea v-model="formData.notes" class="input" rows="2" placeholder="Personal notes..."></textarea>
          </div>
          <div>
            <label class="block text-gray-400 text-sm mb-1">Tags (comma-separated)</label>
            <input v-model="formData.tagsString" type="text" class="input" placeholder="e.g. major, trending, volatile" />
          </div>
          <div class="flex gap-3 mt-6">
            <button type="submit" class="btn btn-primary flex-1">Save</button>
            <button type="button" @click="closeModal" class="btn btn-secondary flex-1">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast.show" class="fixed bottom-4 right-4 px-4 py-3 rounded-lg text-white z-50" :class="{
      'bg-green-600': toast.type === 'success',
      'bg-red-600': toast.type === 'error',
      'bg-blue-600': toast.type === 'info'
    }">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSymbolStore } from '@/stores/symbols'
import { storeToRefs } from 'pinia'

const symbolStore = useSymbolStore()
const { symbols, stats, isLoading, filteredSymbols } = storeToRefs(symbolStore)

// Local state
const searchQuery = ref('')
const categoryFilter = ref('')
const subcategoryFilter = ref('')
const statusFilter = ref('')
const favoritesOnly = ref(false)
const withDataOnly = ref(false)

// Dynamic subcategory options based on selected category
const subcategoryOptions = computed(() => {
  const options = {
    forex: [
      { value: 'major', label: 'Major' },
      { value: 'minor', label: 'Minor' },
      { value: 'exotic', label: 'Exotic' },
    ],
    crypto: [
      { value: 'large_cap', label: 'Large Cap' },
      { value: 'mid_cap', label: 'Mid Cap' },
      { value: 'small_cap', label: 'Small Cap' },
      { value: 'defi', label: 'DeFi' },
      { value: 'meme', label: 'Meme' },
      { value: 'stablecoin', label: 'Stablecoin' },
    ],
    stock: [
      { value: 'tech', label: 'Tech' },
      { value: 'finance', label: 'Finance' },
      { value: 'healthcare', label: 'Healthcare' },
      { value: 'energy', label: 'Energy' },
      { value: 'consumer', label: 'Consumer' },
      { value: 'industrial', label: 'Industrial' },
    ],
    index: [
      { value: 'global', label: 'Global' },
      { value: 'regional', label: 'Regional' },
      { value: 'sector', label: 'Sector' },
    ],
    commodity: [
      { value: 'precious_metal', label: 'Precious Metal' },
      { value: 'base_metal', label: 'Base Metal' },
      { value: 'agriculture', label: 'Agriculture' },
      { value: 'energy_commodity', label: 'Energy' },
    ],
  }
  return categoryFilter.value ? options[categoryFilter.value] || [] : []
})
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingSymbol = ref(null)
const toast = ref({ show: false, message: '', type: 'info' })

const formData = ref({
  symbol: '',
  display_name: '',
  category: 'forex',
  subcategory: '',
  status: 'active',
  base_currency: '',
  quote_currency: '',
  description: '',
  notes: '',
  tagsString: '',
  is_favorite: false,
})

const categoryLabels = {
  forex: 'Forex',
  crypto: 'Crypto',
  stock: 'Stocks',
  index: 'Indices',
  commodity: 'Commodities',
  etf: 'ETF',
  other: 'Other',
}

const subcategoryLabels = {
  // Forex
  major: 'Major',
  minor: 'Minor',
  exotic: 'Exotic',
  // Crypto
  large_cap: 'Large Cap',
  mid_cap: 'Mid Cap',
  small_cap: 'Small Cap',
  defi: 'DeFi',
  meme: 'Meme',
  stablecoin: 'Stablecoin',
  // Stocks
  tech: 'Tech',
  finance: 'Finance',
  healthcare: 'Healthcare',
  energy: 'Energy',
  consumer: 'Consumer',
  industrial: 'Industrial',
  // Indices
  global: 'Global',
  regional: 'Regional',
  sector: 'Sector',
  // Commodities
  precious_metal: 'Precious Metal',
  base_metal: 'Base Metal',
  agriculture: 'Agriculture',
  energy_commodity: 'Energy',
  // General
  other: 'Other',
}

const statusLabels = {
  active: 'Active',
  inactive: 'Inactive',
  suspended: 'Suspended',
}

// Methods
function showToast(message, type = 'info') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}

function formatNumber(num) {
  if (num === null || num === undefined) return '-'
  return num.toLocaleString('de-DE')
}

async function loadSymbols() {
  await symbolStore.fetchSymbols()
  await symbolStore.fetchStats()
}

function handleSearch() {
  symbolStore.setFilters({ search: searchQuery.value })
}

function handleCategoryFilterChange() {
  // Reset subcategory when category changes
  subcategoryFilter.value = ''
  handleFilterChange()
}

function handleFilterChange() {
  symbolStore.setFilters({
    search: searchQuery.value,
    category: categoryFilter.value,
    subcategory: subcategoryFilter.value,
    status: statusFilter.value,
    favorites: favoritesOnly.value,
    withData: withDataOnly.value,
  })
}

async function handleImport() {
  try {
    const result = await symbolStore.importFromTimescaleDB()
    showToast(`Import completed: ${result.imported} new, ${result.updated} updated`, 'success')
  } catch (e) {
    showToast('Import failed: ' + e.message, 'error')
  }
}

async function handleToggleFavorite(symbolId) {
  try {
    await symbolStore.toggleFavorite(symbolId)
  } catch (e) {
    showToast('Failed to update favorite', 'error')
  }
}

async function handleRefresh(symbolId) {
  try {
    await symbolStore.refreshSymbol(symbolId)
    showToast(`${symbolId} refreshed`, 'success')
  } catch (e) {
    showToast('Refresh failed', 'error')
  }
}

async function handleDelete(symbolId) {
  if (!confirm(`Delete symbol ${symbolId}?`)) return
  try {
    await symbolStore.deleteSymbol(symbolId)
    showToast(`${symbolId} deleted`, 'success')
  } catch (e) {
    showToast('Delete failed', 'error')
  }
}

function onCategoryChange() {
  // Reset subcategory when category changes
  formData.value.subcategory = ''
}

function editSymbol(symbol) {
  editingSymbol.value = symbol
  formData.value = {
    symbol: symbol.symbol,
    display_name: symbol.display_name || '',
    category: symbol.category || 'forex',
    subcategory: symbol.subcategory || '',
    status: symbol.status || 'active',
    base_currency: symbol.base_currency || '',
    quote_currency: symbol.quote_currency || '',
    description: symbol.description || '',
    notes: symbol.notes || '',
    tagsString: (symbol.tags || []).join(', '),
    is_favorite: symbol.is_favorite || false,
  }
  showEditModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  showEditModal.value = false
  editingSymbol.value = null
  formData.value = {
    symbol: '',
    display_name: '',
    category: 'forex',
    subcategory: '',
    status: 'active',
    base_currency: '',
    quote_currency: '',
    description: '',
    notes: '',
    tagsString: '',
    is_favorite: false,
  }
}

async function handleSaveSymbol() {
  const data = {
    ...formData.value,
    tags: formData.value.tagsString.split(',').map(t => t.trim()).filter(t => t),
  }
  delete data.tagsString
  // Convert empty subcategory to null
  if (!data.subcategory) {
    data.subcategory = null
  }

  try {
    if (showEditModal.value) {
      await symbolStore.updateSymbol(editingSymbol.value.symbol, data)
      showToast(`${editingSymbol.value.symbol} updated`, 'success')
    } else {
      await symbolStore.createSymbol(data)
      showToast(`${data.symbol} created`, 'success')
    }
    closeModal()
  } catch (e) {
    showToast('Save failed: ' + e.message, 'error')
  }
}

onMounted(() => {
  loadSymbols()
})
</script>
