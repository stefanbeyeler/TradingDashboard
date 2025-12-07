<template>
  <div class="space-y-6">
    <!-- System Status -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">System Status</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="(status, service) in services"
          :key="service"
          class="bg-dark-300 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-gray-400 capitalize">{{ service }}</span>
            <span
              class="w-3 h-3 rounded-full"
              :class="{
                'bg-green-500': status === 'healthy',
                'bg-yellow-500': status === 'degraded',
                'bg-red-500': status === 'unhealthy' || status === 'unavailable',
                'bg-gray-500': status === 'unknown' || status === 'not_configured'
              }"
            ></span>
          </div>
          <p class="text-white font-medium capitalize">{{ status }}</p>
        </div>
      </div>
      <button @click="refreshHealth" :disabled="loading" class="btn btn-secondary mt-4">
        {{ loading ? 'Checking...' : 'Refresh Status' }}
      </button>
    </div>

    <!-- API Configuration -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">API Configuration</h3>
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-sm text-gray-400 block mb-1">KITradingModel API URL</label>
            <input
              type="text"
              :value="config.kitradingUrl"
              disabled
              class="input bg-dark-400"
            />
            <p class="text-xs text-gray-500 mt-1">Configured via backend .env</p>
          </div>
          <div>
            <label class="text-sm text-gray-400 block mb-1">Dashboard API Port</label>
            <input
              type="text"
              value="3010"
              disabled
              class="input bg-dark-400"
            />
            <p class="text-xs text-gray-500 mt-1">Backend server port</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Trading Strategies -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Available Trading Strategies</h3>
      <div v-if="strategies.length" class="space-y-3">
        <div
          v-for="strategy in strategies"
          :key="strategy.id"
          class="flex items-center justify-between p-4 bg-dark-300 rounded-lg"
        >
          <div>
            <h4 class="text-white font-medium">{{ strategy.name }}</h4>
            <p class="text-sm text-gray-400">{{ strategy.type }} | Risk: {{ strategy.risk_level }}</p>
          </div>
          <span
            v-if="strategy.is_default"
            class="badge badge-success"
          >
            Default
          </span>
        </div>
      </div>
      <p v-else class="text-gray-500">No strategies configured</p>
    </div>

    <!-- Forecast Models -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">NHITS Forecast Models</h3>
      <div v-if="forecastModels.length" class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-gray-700">
              <th class="text-left py-2">Symbol</th>
              <th class="text-center py-2">Status</th>
              <th class="text-right py-2">Last Trained</th>
              <th class="text-right py-2">Samples</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="model in forecastModels" :key="model.symbol" class="border-b border-gray-700/50">
              <td class="py-2 text-white">{{ model.symbol }}</td>
              <td class="py-2 text-center">
                <span
                  class="badge"
                  :class="model.model_exists ? 'badge-success' : 'badge-warning'"
                >
                  {{ model.model_exists ? 'Ready' : 'Not Trained' }}
                </span>
              </td>
              <td class="py-2 text-right text-gray-400">
                {{ model.last_trained ? formatDate(model.last_trained) : 'Never' }}
              </td>
              <td class="py-2 text-right text-gray-400">
                {{ model.training_samples || 'N/A' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-gray-500">No forecast models available</p>
    </div>

    <!-- Backup/Restore -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Backup & Restore</h3>
      <p class="text-gray-400 text-sm mb-4">
        Erstellen Sie ein Backup Ihrer Konfiguration, Watchlists, Analysen und Trade-Journal-Einträge.
      </p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <!-- Backup -->
        <div class="bg-dark-300 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Backup erstellen</h4>
          <p class="text-sm text-gray-400 mb-3">
            Exportieren Sie alle Daten als JSON-Datei.
          </p>
          <button
            @click="downloadBackup"
            :disabled="backupLoading"
            class="btn btn-primary w-full"
          >
            {{ backupLoading ? 'Erstelle Backup...' : 'Backup herunterladen' }}
          </button>
        </div>

        <!-- Restore -->
        <div class="bg-dark-300 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Backup wiederherstellen</h4>
          <p class="text-sm text-gray-400 mb-3">
            Importieren Sie Daten aus einer Backup-Datei.
          </p>
          <input
            type="file"
            ref="fileInput"
            accept=".json"
            @change="handleFileSelect"
            class="hidden"
          />
          <button
            @click="$refs.fileInput.click()"
            :disabled="restoreLoading"
            class="btn btn-secondary w-full"
          >
            {{ restoreLoading ? 'Stelle wieder her...' : 'Backup-Datei auswählen' }}
          </button>
        </div>
      </div>

      <!-- Restore Options (shown when file is selected) -->
      <div v-if="selectedBackupFile" class="bg-dark-300 rounded-lg p-4 mb-4">
        <h4 class="text-white font-medium mb-3">Wiederherstellungsoptionen</h4>
        <div class="text-sm text-gray-400 mb-3">
          Datei: {{ selectedBackupFile.name }}
          <span v-if="backupMetadata" class="ml-2">
            ({{ formatDate(backupMetadata.created_at) }})
          </span>
        </div>

        <div v-if="backupMetadata" class="grid grid-cols-2 md:grid-cols-3 gap-2 mb-4">
          <label class="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" v-model="restoreOptions.config" class="form-checkbox" />
            Konfiguration ({{ backupMetadata.record_counts?.config || 0 }})
          </label>
          <label class="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" v-model="restoreOptions.preferences" class="form-checkbox" />
            Einstellungen ({{ backupMetadata.record_counts?.user_preferences || 0 }})
          </label>
          <label class="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" v-model="restoreOptions.watchlists" class="form-checkbox" />
            Watchlists ({{ backupMetadata.record_counts?.watchlists || 0 }})
          </label>
          <label class="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" v-model="restoreOptions.alerts" class="form-checkbox" />
            Preis-Alerts ({{ backupMetadata.record_counts?.price_alerts || 0 }})
          </label>
          <label class="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" v-model="restoreOptions.analyses" class="form-checkbox" />
            Analysen ({{ backupMetadata.record_counts?.trading_analyses || 0 }})
          </label>
          <label class="flex items-center gap-2 text-sm text-gray-300">
            <input type="checkbox" v-model="restoreOptions.journal" class="form-checkbox" />
            Trade Journal ({{ backupMetadata.record_counts?.trade_journal || 0 }})
          </label>
        </div>

        <div class="flex gap-2">
          <button
            @click="executeRestore"
            :disabled="restoreLoading"
            class="btn btn-primary"
          >
            {{ restoreLoading ? 'Wiederherstellen...' : 'Wiederherstellen' }}
          </button>
          <button
            @click="cancelRestore"
            class="btn btn-secondary"
          >
            Abbrechen
          </button>
        </div>
      </div>

      <!-- Restore Result -->
      <div v-if="restoreResult" class="bg-dark-300 rounded-lg p-4">
        <h4 :class="restoreResult.success ? 'text-green-400' : 'text-red-400'" class="font-medium mb-2">
          {{ restoreResult.success ? 'Wiederherstellung erfolgreich' : 'Wiederherstellung fehlgeschlagen' }}
        </h4>
        <div class="text-sm text-gray-400">
          <div v-for="(count, key) in restoreResult.records_restored" :key="key">
            {{ key }}: {{ count }} Einträge wiederhergestellt
          </div>
        </div>
        <div v-if="restoreResult.errors?.length" class="mt-2 text-sm text-red-400">
          <div v-for="error in restoreResult.errors" :key="error">{{ error }}</div>
        </div>
      </div>
    </div>

    <!-- About -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">About</h3>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-400">Dashboard Version</span>
          <span class="text-white">1.0.0</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">Frontend</span>
          <span class="text-white">Vue 3 + Vite + TailwindCSS</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">Backend</span>
          <span class="text-white">FastAPI + Python</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-400">External APIs</span>
          <span class="text-white">CoinGecko, Binance, Alpha Vantage</span>
        </div>
      </div>

      <div class="mt-6 pt-4 border-t border-gray-700">
        <h4 class="text-white font-medium mb-2">API Documentation</h4>
        <div class="flex gap-2">
          <a
            href="/api/docs"
            target="_blank"
            class="btn btn-secondary text-sm"
          >
            Swagger UI
          </a>
          <a
            href="/api/redoc"
            target="_blank"
            class="btn btn-secondary text-sm"
          >
            ReDoc
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useMarketStore } from '@/stores/market'
import * as api from '@/services/api'

const store = useMarketStore()
const loading = ref(false)
const services = ref({})

const strategies = computed(() => store.kiStrategies)
const forecastModels = computed(() => store.forecastModels)

const config = {
  kitradingUrl: 'http://localhost:3011/api/v1',
}

// Backup/Restore state
const backupLoading = ref(false)
const restoreLoading = ref(false)
const selectedBackupFile = ref(null)
const backupData = ref(null)
const backupMetadata = ref(null)
const restoreResult = ref(null)
const fileInput = ref(null)

const restoreOptions = reactive({
  config: true,
  preferences: true,
  watchlists: true,
  alerts: true,
  analyses: true,
  journal: true,
})

async function refreshHealth() {
  loading.value = true
  try {
    const health = await api.getHealth()
    services.value = health.services || {}
  } catch (e) {
    console.error('Failed to refresh health:', e)
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('de-DE')
}

async function downloadBackup() {
  backupLoading.value = true
  try {
    const backup = await api.createBackup()
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    a.download = `trading-dashboard-backup-${timestamp}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Failed to create backup:', e)
    alert('Backup fehlgeschlagen: ' + (e.response?.data?.detail || e.message))
  } finally {
    backupLoading.value = false
  }
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return

  restoreResult.value = null
  selectedBackupFile.value = file

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)
      backupData.value = data
      backupMetadata.value = data.metadata
    } catch (err) {
      alert('Ungültige Backup-Datei')
      cancelRestore()
    }
  }
  reader.readAsText(file)
}

function cancelRestore() {
  selectedBackupFile.value = null
  backupData.value = null
  backupMetadata.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function executeRestore() {
  if (!backupData.value) return

  restoreLoading.value = true
  try {
    const result = await api.restoreBackup(backupData.value, {
      restoreConfig: restoreOptions.config,
      restorePreferences: restoreOptions.preferences,
      restoreWatchlists: restoreOptions.watchlists,
      restoreAlerts: restoreOptions.alerts,
      restoreAnalyses: restoreOptions.analyses,
      restoreJournal: restoreOptions.journal,
    })
    restoreResult.value = result
    cancelRestore()
  } catch (e) {
    console.error('Failed to restore backup:', e)
    restoreResult.value = {
      success: false,
      records_restored: {},
      errors: [e.response?.data?.detail || e.message],
    }
  } finally {
    restoreLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    refreshHealth(),
    store.fetchKIStrategies(),
    store.fetchForecastModels(),
  ])
})
</script>
