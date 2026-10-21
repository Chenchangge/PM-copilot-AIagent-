<script setup>
import { onMounted, ref } from 'vue'

import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { getLearningHistory } from '@/api/profile'
import { getKnowledgeCategoryLabel, getKnowledgeTopicLabel } from '@/utils/knowledge'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const loadingMore = ref(false)
const error = ref('')
const PAGE_SIZE = 20

const statusLabel = { started: '学习中', completed: '已完成' }

function formatTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function load(reset = true) {
  if (reset) {
    loading.value = true
    error.value = ''
    page.value = 1
  } else {
    loadingMore.value = true
  }
  try {
    const data = await getLearningHistory({ page: page.value, page_size: PAGE_SIZE })
    items.value = reset ? data.items || [] : [...items.value, ...(data.items || [])]
    total.value = data.total || 0
  } catch {
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || items.value.length >= total.value) return
  page.value += 1
  await load(false)
}

onMounted(() => load(true))
</script>

<template>
  <div>
    <PageHeader title="学习记录" />

    <div v-if="loading" class="px-5 py-20 text-center text-sm text-gray-400">加载中…</div>

    <div v-else-if="error" class="px-5 py-20 text-center">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="load(true)">重试</button>
    </div>

    <div v-else-if="!items.length" class="px-5">
      <EmptyState title="还没有学习记录" description="开始学习后，你的学习记录会显示在这里" />
    </div>

    <div v-else class="px-5 py-5">
      <p class="text-xs text-gray-400">共 {{ total }} 条学习记录</p>
      <div class="mt-3 space-y-2">
        <RouterLink
          v-for="item in items"
          :key="item.id"
          :to="`/learning/knowledge/${item.knowledge_point_id}`"
          class="card flex items-start justify-between gap-3 p-4 transition-colors hover:border-gray-200"
        >
          <div class="min-w-0">
            <p class="truncate text-sm font-medium text-gray-900">{{ item.title }}</p>
            <p class="mt-1 text-[11px] text-gray-400">
              {{ getKnowledgeCategoryLabel(item.category) }}
              <span v-if="item.topic"> · {{ getKnowledgeTopicLabel(item.topic) }}</span>
              · {{ item.duration_minutes }} 分钟
            </p>
            <p class="mt-1 text-[11px] text-gray-400">
              {{ item.completed_at ? `完成于 ${formatTime(item.completed_at)}` : `开始于 ${formatTime(item.started_at)}` }}
            </p>
          </div>
          <span
            class="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium"
            :class="item.status === 'completed' ? 'bg-green-50 text-green-600' : 'bg-brand-50 text-brand-600'"
          >
            {{ statusLabel[item.status] || item.status }}
          </span>
        </RouterLink>
      </div>

      <button
        v-if="items.length < total"
        type="button"
        class="mt-4 w-full rounded-2xl border border-gray-200 bg-white py-3 text-sm text-gray-600 disabled:text-gray-400"
        :disabled="loadingMore"
        @click="loadMore"
      >
        {{ loadingMore ? '加载中…' : '加载更多' }}
      </button>
    </div>
  </div>
</template>
