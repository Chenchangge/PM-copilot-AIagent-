<script setup>
import { computed, reactive } from 'vue'

import LearningTabs from '@/components/learning/LearningTabs.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { dailyTasks, learningPlanMeta } from '@/mock'

const tasks = reactive(dailyTasks.map((t) => ({ ...t })))
const progress = computed(() => Math.round((learningPlanMeta.currentDay / learningPlanMeta.totalDays) * 100))

function toggle(t) {
  t.done = !t.done
}
</script>

<template>
  <div>
    <LearningTabs />
    <div class="px-5 py-6">
      <h1 class="text-lg font-bold text-gray-900">{{ learningPlanMeta.title }}</h1>

      <section class="mt-6">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-medium text-gray-900">总体进度</h2>
          <span class="text-sm font-semibold text-brand-600">
            Day {{ learningPlanMeta.currentDay }} / {{ learningPlanMeta.totalDays }}
          </span>
        </div>
        <ProgressBar :value="progress" class="mt-3" />
      </section>

      <section class="mt-6">
        <p class="text-xs text-gray-400">今日学习</p>
        <p class="mt-1 text-sm font-medium text-gray-900">{{ learningPlanMeta.todayTopic }}</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="今日任务" />
        <div class="mt-3 space-y-2">
          <button
            v-for="t in tasks"
            :key="t.id"
            type="button"
            class="card flex w-full items-center gap-3 p-4 text-left transition-colors hover:border-gray-200"
            @click="toggle(t)"
          >
            <span
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border"
              :class="t.done ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-300 text-transparent'"
            >
              <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </span>
            <span class="text-sm" :class="t.done ? 'text-gray-400 line-through' : 'text-gray-900'">{{ t.title }}</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
