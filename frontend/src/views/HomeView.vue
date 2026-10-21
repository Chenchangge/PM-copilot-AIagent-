<script setup>
import { onMounted, ref } from 'vue'

import ProgressBar from '@/components/ui/ProgressBar.vue'
import { getHomeSummary } from '@/api/learning'

const summary = ref(null)
const loading = ref(true)
const error = ref('')

const entries = [
  {
    label: '学习',
    desc: '产品知识 · AI问答 · 学习计划',
    to: '/learning/knowledge',
    icon: 'M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25',
  },
  {
    label: '模拟面试',
    desc: 'AI面试 · 能力评估 · 薄弱点分析',
    to: '/interview/setup',
    icon: 'M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z',
  },
]

const actionLabel = (s) => {
  if (!s) return ''
  if (s.recommended_next_action === 'day_done') return '今日学习已完成'
  if (s.recommended_next_action === 'interview') return '计划已完成 · 建议模拟面试'
  return '继续学习'
}

const taskStatusLabel = {
  completed: '已完成',
  in_progress: '学习中',
  pending: '待学习',
  skipped: '已跳过',
}

function taskLink(task) {
  return `/learning/knowledge/${task.knowledge_point_id}?taskId=${task.id}`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    summary.value = await getHomeSummary()
  } catch {
    summary.value = null
    error.value = '首页数据加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="px-5 pt-10 pb-4">
    <div class="flex items-center gap-2">
      <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">P</span>
      <span class="text-base font-bold text-gray-900">PM Copilot</span>
    </div>
    <p class="mt-2 text-sm text-gray-500">AI产品经理学习与模拟面试助手</p>

    <!-- 当前学习计划：loading / error / empty 三态 -->
    <div v-if="loading" class="card mt-6 p-5">
      <p class="text-sm text-gray-400">正在加载学习计划…</p>
    </div>

    <div v-else-if="error" class="card mt-6 p-5">
      <p class="text-sm text-red-500">{{ error }}</p>
      <button type="button" class="mt-2 text-sm font-medium text-brand-600" @click="load">重试</button>
    </div>

    <RouterLink
      v-else-if="summary && summary.active_plan"
      :to="`/learning/plan/${summary.active_plan.id}`"
      class="card mt-6 block p-5 transition-colors hover:border-gray-200"
    >
      <div class="flex items-center justify-between">
        <p class="text-xs font-medium text-brand-600">当前学习计划</p>
        <span class="text-xs text-gray-400">第 {{ summary.active_plan.current_day_number }} / {{ summary.active_plan.selected_days }} 天</span>
      </div>
      <h2 class="mt-1 text-base font-semibold text-gray-900">{{ summary.active_plan.title }}</h2>

      <div class="mt-3 flex items-center gap-2">
        <ProgressBar :value="summary.active_plan.progress_percent" size="sm" class="flex-1" />
        <span class="text-xs text-gray-500">{{ summary.active_plan.progress_percent }}%</span>
      </div>

      <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span>已完成 {{ summary.active_plan.completed_knowledge_points }} / {{ summary.active_plan.total_knowledge_points }} 个知识点</span>
        <span>今日 {{ summary.today_progress.done }} / {{ summary.today_progress.total }} 个任务</span>
      </div>

      <div class="mt-3 flex items-center justify-between rounded-xl bg-brand-50 px-3 py-2.5">
        <span class="text-xs font-medium text-brand-700">{{ actionLabel(summary) }}</span>
        <span class="text-xs text-brand-600">
          {{ summary.recommended_next_action === 'day_done' ? '查看计划' : '继续学习 →' }}
        </span>
      </div>
    </RouterLink>

    <RouterLink
      v-else-if="!loading"
      to="/learning/plan"
      class="card mt-6 flex items-center justify-between p-5 transition-colors hover:border-gray-200"
    >
      <div>
        <p class="text-sm font-semibold text-gray-900">开始一个学习计划</p>
        <p class="mt-1 text-xs text-gray-400">设定目标，系统为你排好每天的学习任务</p>
      </div>
      <svg class="h-5 w-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
    </RouterLink>

    <!-- 今日任务：最多 3 条，直接进入知识点 -->
    <section v-if="summary && summary.active_plan && summary.today_tasks && summary.today_tasks.length" class="mt-3">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold text-gray-900">今日任务</h2>
        <RouterLink :to="`/learning/plan/${summary.active_plan.id}`" class="text-[11px] text-brand-600">
          查看计划
        </RouterLink>
      </div>
      <div class="mt-2 space-y-2">
        <RouterLink
          v-for="t in summary.today_tasks.slice(0, 3)"
          :key="t.id"
          :to="taskLink(t)"
          class="card flex items-center justify-between gap-3 p-3.5 transition-colors hover:border-gray-200"
        >
          <div class="flex min-w-0 items-center gap-2.5">
            <span
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-semibold"
              :class="t.status === 'completed' ? 'border-green-500 bg-green-500 text-white' : 'border-gray-300 bg-white text-gray-400'"
            >
              {{ t.status === 'completed' ? '✓' : '' }}
            </span>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium" :class="t.status === 'completed' ? 'text-gray-400 line-through' : 'text-gray-900'">
                {{ t.title }}
              </p>
              <p class="mt-0.5 text-[11px] text-gray-400">
                {{ t.estimated_minutes }} 分钟 · {{ taskStatusLabel[t.status] || t.status }}
              </p>
            </div>
          </div>
          <svg class="h-4 w-4 shrink-0 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </RouterLink>
      </div>
      <p v-if="summary.today_tasks.length > 3" class="mt-1.5 text-[11px] text-gray-400">
        还有 {{ summary.today_tasks.length - 3 }} 个任务，进入计划查看全部
      </p>
    </section>

    <h2 class="mt-8 text-base font-semibold text-gray-900">今天想做什么？</h2>
    <div class="mt-4 grid grid-cols-2 gap-3">
      <RouterLink
        v-for="e in entries"
        :key="e.label"
        :to="e.to"
        class="card flex flex-col p-5 transition-colors hover:border-gray-200"
      >
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50">
          <svg class="h-6 w-6 text-brand-600" fill="none" viewBox="0 0 24 24" stroke-width="1.6" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" :d="e.icon" />
          </svg>
        </div>
        <p class="mt-4 font-semibold text-gray-900">{{ e.label }}</p>
        <p class="mt-1 text-xs leading-relaxed text-gray-400">{{ e.desc }}</p>
      </RouterLink>
    </div>
  </div>
</template>
