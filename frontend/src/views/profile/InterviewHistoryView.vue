<script setup>
import { onMounted, ref } from 'vue'

import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { getInterviewHistory } from '@/api/profile'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const loadingMore = ref(false)
const error = ref('')
const PAGE_SIZE = 20

const statusLabel = {
  created: '进行中',
  waiting_answer: '进行中',
  completed: '已完成',
  aborted: '已中止',
  failed: '失败',
}

function formatTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function actionTo(item) {
  if (item.can_continue) return `/interview/session/${item.session_id}`
  if (item.can_view_evaluation) return `/interview/${item.session_id}/evaluation`
  return ''
}

function actionLabel(item) {
  if (item.can_continue) return '继续面试'
  if (item.can_view_evaluation) return item.evaluation_status === 'completed' ? '查看评价' : '生成评价'
  return '查看记录'
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
    const data = await getInterviewHistory({ page: page.value, page_size: PAGE_SIZE })
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
    <PageHeader title="面试记录" />

    <div v-if="loading" class="px-5 py-20 text-center text-sm text-gray-400">加载中…</div>

    <div v-else-if="error" class="px-5 py-20 text-center">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="load(true)">重试</button>
    </div>

    <div v-else-if="!items.length" class="px-5">
      <EmptyState title="还没有面试记录" description="完成一次模拟面试后，可以在这里查看记录" />
    </div>

    <div v-else class="px-5 py-5">
      <p class="text-xs text-gray-400">共 {{ total }} 场模拟面试</p>
      <div class="mt-3 space-y-2">
        <component
          :is="actionTo(item) ? 'RouterLink' : 'div'"
          v-for="item in items"
          :key="item.session_id"
          :to="actionTo(item) || undefined"
          class="card block p-4 transition-colors"
          :class="actionTo(item) ? 'hover:border-gray-200' : ''"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-sm font-semibold text-gray-900">{{ item.direction }}</p>
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="item.status === 'completed' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'"
                >
                  {{ statusLabel[item.status] || item.status }}
                </span>
              </div>
              <p class="mt-1 text-[11px] text-gray-400">
                {{ item.difficulty }} · {{ item.interview_type }} · {{ formatTime(item.created_at) }}
              </p>
            </div>
            <div class="shrink-0 text-right">
              <p v-if="item.overall_score !== null" class="text-lg font-semibold text-brand-600">{{ item.overall_score }}</p>
              <p v-else class="text-[11px] text-gray-400">未评价</p>
              <p v-if="item.overall_score !== null" class="text-[10px] text-gray-400">综合评分</p>
            </div>
          </div>

          <div class="mt-3 flex items-center justify-between border-t border-gray-50 pt-2.5">
            <span class="text-[11px] text-gray-400">
              <template v-if="item.can_continue">上次进行到一半，可继续作答</template>
              <template v-else-if="item.can_view_evaluation && item.evaluation_status === 'completed'">查看逐题复盘与参考答案</template>
              <template v-else-if="item.can_view_evaluation">点击生成 AI 评价</template>
              <template v-else>查看记录</template>
            </span>
            <span class="text-xs font-medium text-brand-600">{{ actionLabel(item) }} →</span>
          </div>
        </component>
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
