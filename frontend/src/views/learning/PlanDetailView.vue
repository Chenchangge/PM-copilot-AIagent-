<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import ChoiceGroup from '@/components/ui/ChoiceGroup.vue'
import { getPlan, pausePlan, resumePlan, updatePlan } from '@/api/learning'
import { extractInterviewError } from '@/utils/interview'

const route = useRoute()
const router = useRouter()
const planId = route.params.id

const plan = ref(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)

// 调整计划
const adjusting = ref(false)
const newDaily = ref('30')
const newDays = ref('7')

const statusLabel = { active: '进行中', paused: '已暂停', completed: '已完成', draft: '草稿', abandoned: '已放弃' }
const dayStatusLabel = { completed: '✓ 已完成', in_progress: '进行中', available: '未开始', locked: '未解锁', skipped: '已跳过' }
const taskStatusLabel = { completed: '已完成', in_progress: '学习中', pending: '待学习', skipped: '已跳过' }

const currentDay = computed(() => plan.value?.current_day_number)

async function load() {
  loading.value = true
  error.value = ''
  try {
    plan.value = await getPlan(planId)
    newDaily.value = String(plan.value.daily_minutes)
    newDays.value = String(plan.value.selected_days)
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    loading.value = false
  }
}

async function togglePause() {
  if (busy.value) return
  busy.value = true
  try {
    plan.value = plan.value.status === 'active' ? await pausePlan(planId) : await resumePlan(planId)
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    busy.value = false
  }
}

async function applyAdjust() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    plan.value = await updatePlan(planId, {
      daily_minutes: Number(newDaily.value),
      selected_days: Number(newDays.value),
    })
    adjusting.value = false
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    busy.value = false
  }
}

function openTask(task) {
  router.push(`/learning/knowledge/${task.knowledge_point_id}?taskId=${task.id}`)
}

function goInterview() {
  const rec = plan.value?.recommended_interview
  const q = new URLSearchParams()
  if (rec?.direction) q.set('direction', rec.direction)
  if (rec?.interview_type) q.set('type', rec.interview_type)
  router.push(`/interview/setup?${q.toString()}`)
}

onMounted(load)
</script>

<template>
  <div class="pb-6">
    <PageHeader title="学习计划详情" />

    <div v-if="loading" class="px-5 py-20 text-center text-sm text-gray-400">加载中…</div>

    <div v-else-if="error && !plan" class="px-5 py-20 text-center">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="router.push('/learning/plan')">返回学习计划</button>
    </div>

    <div v-else class="px-5 py-5">
      <div class="card p-5">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-medium text-brand-600">{{ plan.target_name }}</p>
            <h1 class="mt-1 text-lg font-bold text-gray-900">{{ plan.title }}</h1>
          </div>
          <span class="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-500">{{ statusLabel[plan.status] }}</span>
        </div>
        <p class="mt-2 text-xs text-gray-400">
          {{ plan.current_level }} · 每日 {{ plan.daily_minutes }} 分钟 · {{ plan.intensity }}<template v-if="plan.direction_name"> · {{ plan.direction_name }}</template>
        </p>

        <div class="mt-4 flex items-center gap-3">
          <ProgressBar :value="plan.progress_percent" class="flex-1" />
          <span class="text-sm font-semibold text-gray-900">{{ plan.progress_percent }}%</span>
        </div>
        <div class="mt-3 flex justify-between text-xs text-gray-500">
          <span>已完成 {{ plan.completed_knowledge_points }} / {{ plan.total_knowledge_points }} 个知识点</span>
          <span>已学习 {{ plan.completed_minutes }} / {{ plan.total_estimated_minutes }} 分钟</span>
        </div>
      </div>

      <!-- 阶段模拟面试入口 -->
      <div v-if="plan.recommended_interview" class="card mt-4 p-5">
        <p class="text-sm font-semibold text-gray-900">已完成本阶段大部分知识 🎉</p>
        <p class="mt-1 text-xs text-gray-500">建议进行一次模拟面试，检验学习成果。</p>
        <div class="mt-3">
          <PrimaryButton @click="goInterview">开始阶段模拟面试</PrimaryButton>
        </div>
      </div>

      <!-- 操作 -->
      <div class="mt-4 flex gap-2">
        <button
          v-if="plan.status === 'active' || plan.status === 'paused'"
          type="button"
          class="flex-1 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-600"
          @click="togglePause"
        >
          {{ plan.status === 'active' ? '暂停计划' : '恢复计划' }}
        </button>
        <button
          v-if="plan.status === 'active' || plan.status === 'paused'"
          type="button"
          class="flex-1 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-600"
          @click="adjusting = !adjusting"
        >
          调整计划
        </button>
      </div>

      <!-- 调整面板 -->
      <div v-if="adjusting" class="card mt-3 p-5">
        <p class="text-sm font-medium text-gray-900">每日学习时间</p>
        <ChoiceGroup v-model="newDaily" :options="['15', '30', '45', '60']" class="mt-2" />
        <p class="mt-4 text-sm font-medium text-gray-900">剩余学习周期（天）</p>
        <ChoiceGroup v-model="newDays" :options="['5', '7', '10', '14']" class="mt-2" />
        <div class="mt-4 flex gap-2">
          <button type="button" class="flex-1 rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-600" @click="adjusting = false">取消</button>
          <div class="flex-1">
            <PrimaryButton :disabled="busy" @click="applyAdjust">应用</PrimaryButton>
          </div>
        </div>
      </div>

      <!-- Day 列表 -->
      <div class="mt-6 space-y-3">
        <div v-for="day in plan.days" :key="day.id" class="card p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span
                class="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold"
                :class="day.day_number === currentDay ? 'bg-brand-600 text-white' : day.status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'"
              >
                {{ day.day_number }}
              </span>
              <div>
                <p class="text-sm font-medium text-gray-900">Day {{ day.day_number }}</p>
                <p class="text-xs text-gray-400">{{ dayStatusLabel[day.status] }} · {{ day.completed_minutes }}/{{ day.planned_minutes }} 分钟</p>
              </div>
            </div>
            <span v-if="day.progress_percent > 0" class="text-xs text-gray-500">{{ day.progress_percent }}%</span>
          </div>

          <div v-if="day.tasks.length" class="mt-3 space-y-2">
            <button
              v-for="task in day.tasks"
              :key="task.id"
              type="button"
              class="flex w-full items-center justify-between rounded-xl border border-gray-100 bg-gray-50 px-3 py-2.5 text-left transition-colors hover:border-gray-200"
              @click="openTask(task)"
            >
              <div class="flex min-w-0 items-center gap-2">
                <span
                  class="h-4 w-4 shrink-0 rounded-full border"
                  :class="task.status === 'completed' ? 'border-green-500 bg-green-500' : 'border-gray-300 bg-white'"
                >
                  <svg v-if="task.status === 'completed'" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                </span>
                <div class="min-w-0">
                  <p class="truncate text-sm font-medium text-gray-900">{{ task.title }}</p>
                  <p class="text-xs text-gray-400">{{ task.estimated_minutes }} 分钟 · {{ taskStatusLabel[task.status] }}</p>
                </div>
              </div>
              <svg class="h-4 w-4 shrink-0 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
            </button>
          </div>
          <p v-else class="mt-3 text-xs text-gray-400">本日暂无任务</p>
        </div>
      </div>

      <div v-if="error && plan" class="mt-4 rounded-2xl bg-red-50 p-4 text-sm text-red-600">{{ error }}</div>
    </div>
  </div>
</template>
