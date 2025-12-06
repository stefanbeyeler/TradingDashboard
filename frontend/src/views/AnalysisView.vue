<template>
  <div class="space-y-6">
    <!-- Analysis Form -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">KI Trading Analysis</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="text-sm text-gray-400 block mb-1">Symbol</label>
          <select v-model="form.symbol" class="select">
            <option v-for="s in kiSymbols" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div>
          <label class="text-sm text-gray-400 block mb-1">Lookback Days</label>
          <input v-model.number="form.lookbackDays" type="number" min="7" max="90" class="input" />
        </div>
        <div>
          <label class="text-sm text-gray-400 block mb-1">Strategy</label>
          <select v-model="form.strategyId" class="select">
            <option value="">Default</option>
            <option v-for="s in strategies" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <div>
          <label class="text-sm text-gray-400 block mb-1">Use LLM</label>
          <div class="flex items-center gap-3 h-10">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="form.useLlm" class="w-4 h-4 rounded bg-dark-300 border-gray-600" />
              <span class="text-white">Enable AI Analysis</span>
            </label>
          </div>
        </div>
      </div>
      <div class="flex gap-3 mt-4">
        <button @click="runAnalysis" :disabled="isLoading" class="btn btn-primary">
          {{ isLoading ? 'Analyzing...' : 'Run Analysis' }}
        </button>
        <button @click="getQuickRecommendation" :disabled="isLoading" class="btn btn-secondary">
          Quick Recommendation
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="recommendation" class="grid grid-cols-1 lg:grid-cols-3 gap-6 print-area">
      <!-- Main Recommendation -->
      <div class="lg:col-span-2 card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Recommendation: {{ recommendation.symbol }}</h3>
          <div class="flex items-center gap-3">
            <button @click="printAnalysis" class="btn btn-secondary print-hide" title="Print Analysis">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
              </svg>
            </button>
            <span
              class="px-4 py-2 rounded-lg font-bold text-lg"
              :class="{
                'bg-green-500/20 text-green-400 border border-green-500': recommendation.direction === 'LONG',
                'bg-red-500/20 text-red-400 border border-red-500': recommendation.direction === 'SHORT',
                'bg-yellow-500/20 text-yellow-400 border border-yellow-500': recommendation.direction === 'NEUTRAL'
              }"
            >
              {{ recommendation.direction }}
            </span>
          </div>
        </div>

        <!-- Confidence Bar -->
        <div class="mb-6">
          <div class="flex justify-between mb-1">
            <span class="text-gray-400">Confidence Score</span>
            <span class="text-white font-bold">{{ recommendation.confidence_score }}%</span>
          </div>
          <div class="h-3 bg-dark-300 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="{
                'bg-green-500': recommendation.confidence_score >= 70,
                'bg-yellow-500': recommendation.confidence_score >= 40 && recommendation.confidence_score < 70,
                'bg-red-500': recommendation.confidence_score < 40
              }"
              :style="{ width: `${recommendation.confidence_score}%` }"
            ></div>
          </div>
        </div>

        <!-- Price Levels -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-dark-300 p-3 rounded-lg">
            <p class="text-sm text-gray-400">Entry Price</p>
            <p class="text-xl font-mono text-white">{{ formatPrice(recommendation.entry_price) }}</p>
          </div>
          <div class="bg-dark-300 p-3 rounded-lg">
            <p class="text-sm text-gray-400">Stop Loss</p>
            <p class="text-xl font-mono text-red-400">{{ formatPrice(recommendation.stop_loss) }}</p>
          </div>
          <div class="bg-dark-300 p-3 rounded-lg">
            <p class="text-sm text-gray-400">Take Profit 1</p>
            <p class="text-xl font-mono text-green-400">{{ formatPrice(recommendation.take_profit_1) }}</p>
          </div>
          <div class="bg-dark-300 p-3 rounded-lg">
            <p class="text-sm text-gray-400">Risk/Reward</p>
            <p class="text-xl font-mono text-primary-400">{{ recommendation.risk_reward_ratio?.toFixed(2) || 'N/A' }}</p>
          </div>
        </div>

        <!-- Rationale -->
        <div v-if="recommendation.rationale" class="mb-4">
          <h4 class="text-gray-400 mb-2">Analysis Rationale</h4>
          <p class="text-white bg-dark-300 p-4 rounded-lg whitespace-pre-wrap">{{ recommendation.rationale }}</p>
        </div>

        <!-- Risks -->
        <div v-if="recommendation.risks?.length">
          <h4 class="text-gray-400 mb-2">Identified Risks</h4>
          <ul class="space-y-1">
            <li v-for="risk in recommendation.risks" :key="risk" class="flex items-start gap-2 text-gray-300">
              <span class="text-red-400 mt-1">!</span>
              {{ risk }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Side Panel -->
      <div class="space-y-6">
        <!-- Key Levels -->
        <div class="card">
          <h4 class="text-white font-semibold mb-3">Key Levels</h4>
          <div class="space-y-2">
            <template v-if="typeof recommendation.key_levels === 'string'">
              <p class="text-white text-sm">{{ recommendation.key_levels }}</p>
            </template>
            <template v-else-if="Array.isArray(recommendation.key_levels) && recommendation.key_levels.length">
              <div v-for="(level, i) in recommendation.key_levels" :key="i" class="flex justify-between">
                <span class="text-gray-400">Level {{ i + 1 }}</span>
                <span class="text-white font-mono">{{ formatPrice(level) }}</span>
              </div>
            </template>
            <div v-else class="text-gray-500 text-sm">
              No key levels identified
            </div>
          </div>
        </div>

        <!-- Take Profits -->
        <div class="card">
          <h4 class="text-white font-semibold mb-3">Take Profit Targets</h4>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-gray-400">TP1</span>
              <span class="text-green-400 font-mono">{{ formatPrice(recommendation.take_profit_1) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">TP2</span>
              <span class="text-green-400 font-mono">{{ formatPrice(recommendation.take_profit_2) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">TP3</span>
              <span class="text-green-400 font-mono">{{ formatPrice(recommendation.take_profit_3) }}</span>
            </div>
          </div>
        </div>

        <!-- Timestamp -->
        <div class="card">
          <h4 class="text-white font-semibold mb-3">Analysis Info</h4>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Generated</span>
              <span class="text-white">{{ formatTimestamp(recommendation.timestamp) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">LLM Used</span>
              <span class="text-white">{{ form.useLlm ? 'Yes' : 'No' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
      </svg>
      <h3 class="text-xl text-gray-400 mb-2">No Analysis Yet</h3>
      <p class="text-gray-500">Select a symbol and run an analysis to see recommendations</p>
    </div>

    <!-- Query History -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Recent Queries</h3>
      <div v-if="queryLogs.length" class="space-y-2">
        <div
          v-for="log in queryLogs.slice(0, 10)"
          :key="log.id"
          class="flex items-center justify-between p-3 bg-dark-300 rounded-lg"
        >
          <div>
            <span class="text-white font-medium">{{ log.symbol }}</span>
            <span class="text-gray-400 text-sm ml-2">{{ log.query_type }}</span>
          </div>
          <span class="text-gray-500 text-sm">{{ formatTimestamp(log.timestamp) }}</span>
        </div>
      </div>
      <p v-else class="text-gray-500 text-center py-4">No query history available</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useMarketStore } from '@/stores/market'
import * as api from '@/services/api'

const store = useMarketStore()

const form = reactive({
  symbol: 'BTCUSDT',
  lookbackDays: 30,
  strategyId: '',
  useLlm: false,
})

const recommendation = ref(null)
const queryLogs = ref([])

const kiSymbols = computed(() => store.kiSymbols)
const strategies = computed(() => store.kiStrategies)
const isLoading = computed(() => store.isLoading)

async function runAnalysis() {
  try {
    const result = await store.analyzeSymbol({
      symbol: form.symbol,
      lookback_days: form.lookbackDays,
      include_technical: true,
      strategy_id: form.strategyId || undefined,
    })
    if (result?.recommendation) {
      recommendation.value = result.recommendation
    }
    await loadQueryLogs()
  } catch (e) {
    console.error('Analysis failed:', e)
  }
}

async function getQuickRecommendation() {
  try {
    recommendation.value = await store.fetchRecommendation(
      form.symbol,
      form.useLlm,
      form.strategyId || null
    )
    await loadQueryLogs()
  } catch (e) {
    console.error('Quick recommendation failed:', e)
  }
}

async function loadQueryLogs() {
  try {
    const data = await api.getQueryLogs(20)
    queryLogs.value = data.logs || []
  } catch (e) {
    console.error('Failed to load query logs:', e)
  }
}

function formatPrice(value) {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'string') return value
  if (typeof value !== 'number' || isNaN(value)) return 'N/A'
  if (value < 0.01) return `$${value.toFixed(6)}`
  if (value < 1) return `$${value.toFixed(4)}`
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatTimestamp(ts) {
  if (!ts) return ''
  const date = new Date(ts)
  return date.toLocaleString('de-DE')
}

function printAnalysis() {
  const printContent = document.querySelector('.print-area')
  if (!printContent) return

  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    alert('Bitte erlauben Sie Pop-ups für diese Seite')
    return
  }

  const rec = recommendation.value
  const directionColor = rec.direction === 'LONG' ? '#22c55e' : rec.direction === 'SHORT' ? '#ef4444' : '#eab308'
  const confidenceColor = rec.confidence_score >= 70 ? '#22c55e' : rec.confidence_score >= 40 ? '#eab308' : '#ef4444'

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>KI Trading Analysis - ${rec.symbol}</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; color: #1f2937; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #e5e7eb; padding-bottom: 20px; }
        .logo { font-size: 24px; font-weight: bold; }
        .date { color: #6b7280; }
        .symbol-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        .symbol { font-size: 28px; font-weight: bold; }
        .direction { padding: 8px 20px; border-radius: 8px; font-weight: bold; font-size: 18px; color: white; background: ${directionColor}; }
        .section { margin-bottom: 24px; }
        .section-title { font-size: 14px; color: #6b7280; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .confidence-bar { height: 12px; background: #e5e7eb; border-radius: 6px; overflow: hidden; margin-top: 8px; }
        .confidence-fill { height: 100%; background: ${confidenceColor}; width: ${rec.confidence_score}%; }
        .confidence-value { font-size: 24px; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat-box { background: #f9fafb; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb; }
        .stat-label { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
        .stat-value { font-size: 20px; font-weight: bold; font-family: monospace; }
        .stat-value.green { color: #22c55e; }
        .stat-value.red { color: #ef4444; }
        .rationale { background: #f9fafb; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; white-space: pre-wrap; line-height: 1.6; }
        .risks { list-style: none; }
        .risks li { padding: 8px 0; border-bottom: 1px solid #e5e7eb; display: flex; align-items: flex-start; gap: 8px; }
        .risks li:last-child { border-bottom: none; }
        .risk-icon { color: #ef4444; font-weight: bold; }
        .tp-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px; text-align: center; }
        @media print { body { padding: 20px; } }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="logo">Trading Dashboard - KI Analysis</div>
        <div class="date">Generated: ${formatTimestamp(rec.timestamp)}</div>
      </div>

      <div class="symbol-header">
        <div class="symbol">${rec.symbol}</div>
        <div class="direction">${rec.direction}</div>
      </div>

      <div class="section">
        <div class="section-title">Confidence Score</div>
        <div class="confidence-value">${rec.confidence_score}%</div>
        <div class="confidence-bar"><div class="confidence-fill"></div></div>
      </div>

      <div class="grid">
        <div class="stat-box">
          <div class="stat-label">Entry Price</div>
          <div class="stat-value">${formatPrice(rec.entry_price)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Stop Loss</div>
          <div class="stat-value red">${formatPrice(rec.stop_loss)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Take Profit 1</div>
          <div class="stat-value green">${formatPrice(rec.take_profit_1)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Risk/Reward</div>
          <div class="stat-value">${rec.risk_reward_ratio?.toFixed(2) || 'N/A'}</div>
        </div>
      </div>

      <div class="tp-grid">
        <div class="stat-box">
          <div class="stat-label">Take Profit 1</div>
          <div class="stat-value green">${formatPrice(rec.take_profit_1)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Take Profit 2</div>
          <div class="stat-value green">${formatPrice(rec.take_profit_2)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Take Profit 3</div>
          <div class="stat-value green">${formatPrice(rec.take_profit_3)}</div>
        </div>
      </div>

      ${rec.rationale ? `
      <div class="section" style="margin-top: 24px;">
        <div class="section-title">Analysis Rationale</div>
        <div class="rationale">${rec.rationale}</div>
      </div>
      ` : ''}

      ${rec.risks?.length ? `
      <div class="section">
        <div class="section-title">Identified Risks</div>
        <ul class="risks">
          ${rec.risks.map(risk => `<li><span class="risk-icon">!</span> ${risk}</li>`).join('')}
        </ul>
      </div>
      ` : ''}

      <div class="footer">
        This analysis was generated by KI Trading Model. Past performance does not guarantee future results.
        Trading involves risk. Please trade responsibly.
      </div>
    </body>
    </html>
  `)

  printWindow.document.close()
  printWindow.focus()
  setTimeout(() => {
    printWindow.print()
  }, 250)
}

onMounted(async () => {
  await store.fetchKIStrategies()
  await loadQueryLogs()
  if (store.kiSymbols.length > 0) {
    form.symbol = store.kiSymbols[0]
  }
})
</script>
