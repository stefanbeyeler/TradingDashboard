<template>
  <div class="space-y-6">
    <!-- Forecast Controls -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">NHITS Price Forecast</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="text-sm text-gray-400 block mb-1">Symbol</label>
          <select v-model="selectedSymbol" class="select">
            <option v-for="m in forecastModels" :key="m.symbol" :value="m.symbol">
              {{ m.symbol }} {{ m.model_exists ? '' : '(no model)' }}
            </option>
          </select>
        </div>
        <div>
          <label class="text-sm text-gray-400 block mb-1">Horizon (hours)</label>
          <select v-model.number="horizon" class="select">
            <option :value="6">6 hours</option>
            <option :value="12">12 hours</option>
            <option :value="24">24 hours</option>
            <option :value="48">48 hours</option>
            <option :value="72">72 hours</option>
            <option :value="168">7 days</option>
          </select>
        </div>
        <div class="flex items-end">
          <button @click="loadForecast" :disabled="isLoading" class="btn btn-primary w-full">
            {{ isLoading ? 'Loading...' : 'Generate Forecast' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Forecast Result -->
    <div v-if="forecast" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Chart Area -->
      <div class="lg:col-span-2 card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Price Prediction: {{ forecast.symbol }}</h3>
          <div class="flex items-center gap-2">
            <span class="text-gray-400">Current:</span>
            <span class="text-2xl font-mono text-white">{{ formatPrice(forecast.current_price) }}</span>
          </div>
        </div>

        <!-- Simple Chart Visualization -->
        <div class="bg-dark-300 rounded-lg p-4 h-80">
          <div class="h-full flex flex-col">
            <!-- Y-Axis Labels and Chart -->
            <div class="flex-1 flex">
              <!-- Y-Axis -->
              <div class="w-20 flex flex-col justify-between text-right pr-2 text-xs text-gray-400">
                <span>{{ formatPrice(chartMax) }}</span>
                <span>{{ formatPrice((chartMax + chartMin) / 2) }}</span>
                <span>{{ formatPrice(chartMin) }}</span>
              </div>
              <!-- Chart Area -->
              <div class="flex-1 relative border-l border-b border-gray-600">
                <!-- Current Price Line -->
                <div
                  class="absolute left-0 right-0 border-t border-dashed border-primary-500 z-10"
                  :style="{ top: `${(1 - (forecast.current_price - chartMin) / (chartMax - chartMin)) * 100}%` }"
                >
                  <span class="absolute right-0 -top-3 text-xs text-primary-400 bg-dark-300 px-1">Current</span>
                </div>

                <!-- Prediction Points -->
                <svg class="absolute inset-0 w-full h-full overflow-visible">
                  <!-- Confidence Band -->
                  <path
                    :d="confidenceBandPath"
                    fill="rgba(59, 130, 246, 0.1)"
                    stroke="none"
                  />
                  <!-- Prediction Line -->
                  <path
                    :d="predictionLinePath"
                    fill="none"
                    stroke="#3b82f6"
                    stroke-width="2"
                  />
                  <!-- Prediction Points -->
                  <circle
                    v-for="(point, i) in chartPoints"
                    :key="i"
                    :cx="`${point.x}%`"
                    :cy="`${point.y}%`"
                    r="4"
                    fill="#3b82f6"
                  />
                </svg>
              </div>
            </div>
            <!-- X-Axis Labels -->
            <div class="h-6 flex ml-20">
              <div class="flex-1 flex justify-between text-xs text-gray-400 pt-1">
                <span>Now</span>
                <span>+{{ Math.floor(horizon / 2) }}h</span>
                <span>+{{ horizon }}h</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Predictions Table -->
        <div class="mt-4 overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-gray-400 border-b border-gray-700">
                <th class="text-left py-2">Time</th>
                <th class="text-right py-2">Predicted Price</th>
                <th class="text-right py-2">Low (10%)</th>
                <th class="text-right py-2">High (90%)</th>
                <th class="text-right py-2">Change</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pred in forecast.predictions" :key="pred.timestamp" class="border-b border-gray-700/50">
                <td class="py-2 text-gray-300">{{ formatTime(pred.timestamp) }}</td>
                <td class="py-2 text-right font-mono text-white">{{ formatPrice(pred.predicted_price) }}</td>
                <td class="py-2 text-right font-mono text-gray-400">{{ formatPrice(pred.confidence_low) }}</td>
                <td class="py-2 text-right font-mono text-gray-400">{{ formatPrice(pred.confidence_high) }}</td>
                <td
                  class="py-2 text-right font-mono"
                  :class="getChangeClass(pred.predicted_price)"
                >
                  {{ formatChange(pred.predicted_price) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Forecast Details -->
      <div class="space-y-6">
        <!-- Trend Probabilities -->
        <div class="card">
          <h4 class="text-white font-semibold mb-4">Trend Probability</h4>
          <div class="space-y-4">
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-green-400">Bullish</span>
                <span class="text-white">{{ (forecast.trend_probability_up * 100).toFixed(1) }}%</span>
              </div>
              <div class="h-2 bg-dark-300 rounded-full overflow-hidden">
                <div
                  class="h-full bg-green-500 rounded-full"
                  :style="{ width: `${forecast.trend_probability_up * 100}%` }"
                ></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-red-400">Bearish</span>
                <span class="text-white">{{ (forecast.trend_probability_down * 100).toFixed(1) }}%</span>
              </div>
              <div class="h-2 bg-dark-300 rounded-full overflow-hidden">
                <div
                  class="h-full bg-red-500 rounded-full"
                  :style="{ width: `${forecast.trend_probability_down * 100}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Model Confidence -->
        <div class="card">
          <h4 class="text-white font-semibold mb-4">Model Confidence</h4>
          <div class="text-center">
            <div class="text-4xl font-bold text-primary-400 mb-2">
              {{ ((forecast.model_confidence || 0) * 100).toFixed(0) }}%
            </div>
            <p class="text-gray-400 text-sm">Based on historical accuracy</p>
          </div>
        </div>

        <!-- Price Summary -->
        <div class="card">
          <h4 class="text-white font-semibold mb-4">Price Summary</h4>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-400">Current</span>
              <span class="text-white font-mono">{{ formatPrice(forecast.current_price) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Predicted ({{ horizon }}h)</span>
              <span class="text-primary-400 font-mono">{{ formatPrice(lastPrediction?.predicted_price) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Expected Change</span>
              <span
                class="font-mono"
                :class="getChangeClass(lastPrediction?.predicted_price)"
              >
                {{ formatChange(lastPrediction?.predicted_price) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Generated Info -->
        <div class="card">
          <h4 class="text-white font-semibold mb-3">Forecast Info</h4>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Generated</span>
              <span class="text-white">{{ formatTimestamp(forecast.generated_at) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Horizon</span>
              <span class="text-white">{{ horizon }} hours</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Data Points</span>
              <span class="text-white">{{ forecast.predictions?.length || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path>
      </svg>
      <h3 class="text-xl text-gray-400 mb-2">No Forecast Generated</h3>
      <p class="text-gray-500">Select a symbol and generate a forecast to see predictions</p>
    </div>

    <!-- Available Models -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Available NHITS Models</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="model in forecastModels"
          :key="model.symbol"
          class="p-4 bg-dark-300 rounded-lg cursor-pointer hover:bg-dark-200 transition-colors"
          :class="{ 'border border-primary-500': selectedSymbol === model.symbol }"
          @click="selectedSymbol = model.symbol"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-semibold text-white">{{ model.symbol }}</span>
            <span
              class="badge"
              :class="model.model_exists ? 'badge-success' : 'badge-warning'"
            >
              {{ model.model_exists ? 'Ready' : 'No Model' }}
            </span>
          </div>
          <div v-if="model.last_trained" class="text-sm text-gray-400">
            Last trained: {{ formatTimestamp(model.last_trained) }}
          </div>
          <div v-if="model.training_samples" class="text-sm text-gray-400">
            Samples: {{ model.training_samples }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMarketStore } from '@/stores/market'

const store = useMarketStore()

const selectedSymbol = ref('')
const horizon = ref(24)
const forecast = ref(null)

const forecastModels = computed(() => store.forecastModels)
const isLoading = computed(() => store.isLoading)

const lastPrediction = computed(() => {
  if (!forecast.value?.predictions?.length) return null
  return forecast.value.predictions[forecast.value.predictions.length - 1]
})

// Chart calculations
const chartMin = computed(() => {
  if (!forecast.value?.predictions?.length) return 0
  const prices = forecast.value.predictions.map(p => p.confidence_low || p.predicted_price)
  return Math.min(forecast.value.current_price, ...prices) * 0.995
})

const chartMax = computed(() => {
  if (!forecast.value?.predictions?.length) return 0
  const prices = forecast.value.predictions.map(p => p.confidence_high || p.predicted_price)
  return Math.max(forecast.value.current_price, ...prices) * 1.005
})

const chartPoints = computed(() => {
  if (!forecast.value?.predictions?.length) return []
  const range = chartMax.value - chartMin.value
  return forecast.value.predictions.map((p, i) => ({
    x: ((i + 1) / forecast.value.predictions.length) * 100,
    y: (1 - (p.predicted_price - chartMin.value) / range) * 100,
  }))
})

const predictionLinePath = computed(() => {
  if (!chartPoints.value.length) return ''
  const points = chartPoints.value
  return `M ${points[0].x} ${points[0].y} ` + points.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ')
})

const confidenceBandPath = computed(() => {
  if (!forecast.value?.predictions?.length) return ''
  const preds = forecast.value.predictions
  const range = chartMax.value - chartMin.value

  const upperPoints = preds.map((p, i) => ({
    x: ((i + 1) / preds.length) * 100,
    y: (1 - ((p.confidence_high || p.predicted_price) - chartMin.value) / range) * 100,
  }))

  const lowerPoints = preds.map((p, i) => ({
    x: ((i + 1) / preds.length) * 100,
    y: (1 - ((p.confidence_low || p.predicted_price) - chartMin.value) / range) * 100,
  })).reverse()

  const all = [...upperPoints, ...lowerPoints]
  return `M ${all[0].x} ${all[0].y} ` + all.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ') + ' Z'
})

async function loadForecast() {
  if (!selectedSymbol.value) return
  try {
    forecast.value = await store.fetchForecast(selectedSymbol.value, horizon.value)
  } catch (e) {
    console.error('Failed to load forecast:', e)
  }
}

function formatPrice(value) {
  if (!value) return 'N/A'
  if (value < 0.01) return `$${value.toFixed(6)}`
  if (value < 1) return `$${value.toFixed(4)}`
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatChange(predictedPrice) {
  if (!predictedPrice || !forecast.value?.current_price) return 'N/A'
  const change = ((predictedPrice - forecast.value.current_price) / forecast.value.current_price) * 100
  return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`
}

function getChangeClass(predictedPrice) {
  if (!predictedPrice || !forecast.value?.current_price) return 'text-gray-400'
  return predictedPrice >= forecast.value.current_price ? 'text-green-400' : 'text-red-400'
}

function formatTime(ts) {
  if (!ts) return ''
  const date = new Date(ts)
  return date.toLocaleString('de-DE', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' })
}

function formatTimestamp(ts) {
  if (!ts) return ''
  const date = new Date(ts)
  return date.toLocaleString('de-DE')
}

onMounted(async () => {
  await store.fetchForecastModels()
  if (store.forecastModels.length > 0) {
    const available = store.forecastModels.find(m => m.model_exists)
    selectedSymbol.value = available?.symbol || store.forecastModels[0].symbol
  }
})
</script>
