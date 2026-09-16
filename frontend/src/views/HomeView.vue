<script setup>
import ProgressBar from '@/components/ui/ProgressBar.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { continueLearning } from '@/mock'

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
</script>

<template>
  <div class="px-5 pt-10">
    <div class="flex items-center gap-2">
      <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">P</span>
      <span class="text-base font-bold text-gray-900">PM Copilot</span>
    </div>
    <p class="mt-2 text-sm text-gray-500">AI 产品经理学习与模拟面试助手</p>

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

    <section class="mt-8">
      <SectionTitle title="继续学习" />
      <div class="mt-3 space-y-2">
        <RouterLink
          v-for="c in continueLearning"
          :key="c.id"
          :to="`/learning/knowledge/${c.id}`"
          class="card block p-4 transition-colors hover:border-gray-200"
        >
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-900">{{ c.title }}</span>
            <span class="text-xs text-gray-400">{{ c.progress }}%</span>
          </div>
          <ProgressBar :value="c.progress" size="sm" class="mt-2" />
        </RouterLink>
      </div>
    </section>
  </div>
</template>
