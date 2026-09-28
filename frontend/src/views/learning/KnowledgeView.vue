<script setup>
import { computed, onMounted, ref } from 'vue'

import LearningTabs from '@/components/learning/LearningTabs.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import KnowledgeItem from '@/components/ui/KnowledgeItem.vue'
import { listKnowledge } from '@/api/knowledge'
import { KNOWLEDGE_CATEGORY_LABELS, getKnowledgeCategoryLabel, getKnowledgeTopicLabel } from '@/utils/knowledge'

const items = ref([])
const loading = ref(true)
const error = ref('')
const active = ref('全部')
const topicActive = ref('全部')
const keyword = ref('')

const categories = computed(() => {
  const present = new Set(items.value.map((k) => k.category))
  const labels = Object.entries(KNOWLEDGE_CATEGORY_LABELS)
    .filter(([slug]) => present.has(slug))
    .map(([, label]) => label)
  return ['全部', ...labels]
})

// 当前分类下的二级主题（按 slug 去重，展示中文标签）
const topics = computed(() => {
  const present = new Set()
  for (const k of items.value) {
    if (active.value !== '全部' && getKnowledgeCategoryLabel(k.category) !== active.value) continue
    if (k.topic) present.add(k.topic)
  }
  return [{ id: '全部', label: '全部' }, ...[...present].map((t) => ({ id: t, label: getKnowledgeTopicLabel(t) }))]
})

const filtered = computed(() => {
  const kw = keyword.value.trim()
  let list = items.value
  if (active.value !== '全部') {
    list = list.filter((k) => getKnowledgeCategoryLabel(k.category) === active.value)
  }
  if (topicActive.value !== '全部') {
    list = list.filter((k) => k.topic === topicActive.value)
  }
  if (kw) {
    list = list.filter((k) => k.title.includes(kw) || (k.tags || []).some((t) => t.includes(kw)))
  }
  return list
})

function pickCategory(label) {
  active.value = label
  topicActive.value = '全部'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await listKnowledge()
    items.value = data.items || []
  } catch {
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="px-5 pt-5">
      <h1 class="text-xl font-bold text-gray-900">学习</h1>
    </div>

    <LearningTabs />

    <div v-if="loading" class="px-5 py-16 text-center text-sm text-gray-400">加载中…</div>

    <div v-else-if="error" class="px-5 py-16 text-center">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="load">重新加载</button>
    </div>

    <div v-else class="px-5 py-4">
      <div class="relative">
        <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索产品知识"
          class="w-full rounded-full border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-brand-500 focus:outline-none"
        />
      </div>

      <div class="mt-4 flex gap-2 overflow-x-auto pb-1">
        <button
          v-for="c in categories"
          :key="c"
          type="button"
          class="shrink-0 rounded-full border px-4 py-1.5 text-sm transition-colors"
          :class="active === c ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
          @click="pickCategory(c)"
        >
          {{ c }}
        </button>
      </div>

      <div v-if="topics.length > 1" class="mt-2 flex gap-2 overflow-x-auto pb-1">
        <button
          v-for="t in topics"
          :key="t.id"
          type="button"
          class="shrink-0 rounded-full border px-3 py-1 text-xs transition-colors"
          :class="topicActive === t.id ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-100 bg-white text-gray-500 active:bg-gray-50'"
          @click="topicActive = t.id"
        >
          {{ t.label }}
        </button>
      </div>

      <div v-if="filtered.length" class="mt-4 space-y-3">
        <KnowledgeItem v-for="k in filtered" :key="k.id" :item="k" :to="`/learning/knowledge/${k.id}`" />
      </div>
      <EmptyState v-else title="没有找到相关知识" description="换个关键词或分类试试" />
    </div>
  </div>
</template>
