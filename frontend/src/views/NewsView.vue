<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="card">
      <div class="flex flex-wrap gap-4 items-center justify-between">
        <h3 class="text-lg font-semibold text-white">Market News</h3>
        <div class="flex gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id; loadNews()"
            class="btn"
            :class="activeTab === tab.id ? 'btn-primary' : 'btn-secondary'"
          >
            {{ tab.name }}
          </button>
          <button @click="loadNews" :disabled="loading" class="btn btn-secondary">
            {{ loading ? 'Loading...' : 'Refresh' }}
          </button>
        </div>
      </div>
    </div>

    <!-- News Grid -->
    <div v-if="news.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <a
        v-for="article in news"
        :key="article.url"
        :href="article.url"
        target="_blank"
        rel="noopener noreferrer"
        class="card hover:border-primary-500 transition-colors group"
      >
        <!-- Header -->
        <div class="flex items-center justify-between mb-3">
          <span
            class="badge"
            :class="{
              'badge-success': article.sentiment === 'positive',
              'badge-danger': article.sentiment === 'negative',
              'badge-info': article.sentiment === 'neutral' || !article.sentiment
            }"
          >
            {{ article.sentiment || 'neutral' }}
          </span>
          <span class="text-xs text-gray-500">{{ article.source }}</span>
        </div>

        <!-- Title -->
        <h4 class="text-white font-semibold mb-2 group-hover:text-primary-400 transition-colors line-clamp-2">
          {{ article.title }}
        </h4>

        <!-- Description -->
        <p class="text-gray-400 text-sm mb-4 line-clamp-3">
          {{ article.description }}
        </p>

        <!-- Footer -->
        <div class="flex items-center justify-between mt-auto pt-3 border-t border-gray-700">
          <span class="text-xs text-gray-500">
            {{ formatDate(article.published_at) }}
          </span>
          <div v-if="article.related_symbols?.length" class="flex gap-1">
            <span
              v-for="symbol in article.related_symbols.slice(0, 3)"
              :key="symbol"
              class="text-xs px-1.5 py-0.5 bg-dark-300 rounded text-gray-400"
            >
              {{ symbol }}
            </span>
          </div>
        </div>
      </a>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="card text-center py-12">
      <div class="animate-spin w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4"></div>
      <p class="text-gray-400">Loading news...</p>
    </div>

    <!-- Empty State -->
    <div v-else class="card text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
      </svg>
      <h3 class="text-xl text-gray-400 mb-2">No News Available</h3>
      <p class="text-gray-500">Try refreshing or selecting a different category</p>
    </div>

    <!-- Sentiment Summary -->
    <div v-if="news.length" class="card">
      <h3 class="text-lg font-semibold text-white mb-4">Sentiment Analysis</h3>
      <div class="grid grid-cols-3 gap-4">
        <div class="text-center p-4 bg-dark-300 rounded-lg">
          <div class="text-3xl font-bold text-green-400 mb-1">{{ sentimentCounts.positive }}</div>
          <p class="text-gray-400 text-sm">Positive</p>
          <div class="mt-2 h-1 bg-dark-400 rounded-full overflow-hidden">
            <div
              class="h-full bg-green-500 rounded-full"
              :style="{ width: `${(sentimentCounts.positive / news.length) * 100}%` }"
            ></div>
          </div>
        </div>
        <div class="text-center p-4 bg-dark-300 rounded-lg">
          <div class="text-3xl font-bold text-blue-400 mb-1">{{ sentimentCounts.neutral }}</div>
          <p class="text-gray-400 text-sm">Neutral</p>
          <div class="mt-2 h-1 bg-dark-400 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 rounded-full"
              :style="{ width: `${(sentimentCounts.neutral / news.length) * 100}%` }"
            ></div>
          </div>
        </div>
        <div class="text-center p-4 bg-dark-300 rounded-lg">
          <div class="text-3xl font-bold text-red-400 mb-1">{{ sentimentCounts.negative }}</div>
          <p class="text-gray-400 text-sm">Negative</p>
          <div class="mt-2 h-1 bg-dark-400 rounded-full overflow-hidden">
            <div
              class="h-full bg-red-500 rounded-full"
              :style="{ width: `${(sentimentCounts.negative / news.length) * 100}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Overall Sentiment -->
      <div class="mt-4 p-4 bg-dark-300 rounded-lg">
        <div class="flex items-center justify-between">
          <span class="text-gray-400">Overall Market Sentiment</span>
          <span
            class="text-lg font-semibold"
            :class="{
              'text-green-400': overallSentiment === 'Bullish',
              'text-red-400': overallSentiment === 'Bearish',
              'text-blue-400': overallSentiment === 'Neutral'
            }"
          >
            {{ overallSentiment }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import * as api from '@/services/api'

const activeTab = ref('crypto')
const news = ref([])
const loading = ref(false)

const tabs = [
  { id: 'crypto', name: 'Crypto' },
  { id: 'combined', name: 'All Markets' },
]

const sentimentCounts = computed(() => {
  const counts = { positive: 0, neutral: 0, negative: 0 }
  news.value.forEach(article => {
    const sentiment = article.sentiment || 'neutral'
    counts[sentiment]++
  })
  return counts
})

const overallSentiment = computed(() => {
  const { positive, negative, neutral } = sentimentCounts.value
  if (positive > negative + neutral / 2) return 'Bullish'
  if (negative > positive + neutral / 2) return 'Bearish'
  return 'Neutral'
})

async function loadNews() {
  loading.value = true
  try {
    if (activeTab.value === 'crypto') {
      news.value = await api.getCryptoNews(30)
    } else {
      news.value = await api.getCombinedNews(30)
    }
  } catch (e) {
    console.error('Failed to load news:', e)
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 1) {
    const diffMins = Math.floor(diffMs / (1000 * 60))
    return `${diffMins}m ago`
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) {
    return `${diffDays}d ago`
  }
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: 'short' })
}

onMounted(() => {
  loadNews()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
