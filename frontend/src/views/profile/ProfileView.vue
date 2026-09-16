<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { mockProfile, mockStats } from '@/mock'

const menu = [
  { label: '学习记录', to: '/profile/learning-history' },
  { label: '面试记录', to: '/profile/interview-history' },
  { label: '设置', to: '/profile/settings' },
]

const overview = [
  { label: '已学习知识点', value: mockStats.learnedCount },
  { label: '完成学习计划', value: mockStats.completedPlans },
  { label: '完成模拟面试', value: mockStats.interviewCount },
]
</script>

<template>
  <div>
    <PageHeader title="我的" :back="false" />
    <div class="px-5 py-6">
      <div class="flex items-center gap-4">
        <div
          class="flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-lg font-semibold text-brand-700"
        >
          {{ mockProfile.name.slice(0, 1) }}
        </div>
        <div>
          <p class="text-lg font-semibold text-gray-900">{{ mockProfile.name }}</p>
          <p class="text-sm text-gray-500">{{ mockProfile.targetRole }} · {{ mockProfile.level }}</p>
        </div>
      </div>

      <section class="mt-6">
        <SectionTitle title="学习概况" />
        <div class="mt-3 flex gap-6">
          <div v-for="o in overview" :key="o.label">
            <p class="text-xl font-bold text-brand-600">{{ o.value }}</p>
            <p class="text-xs text-gray-500">{{ o.label }}</p>
          </div>
        </div>
      </section>

      <div class="mt-8 space-y-3">
        <RouterLink
          v-for="m in menu"
          :key="m.to"
          :to="m.to"
          class="card flex items-center justify-between p-4 transition-colors hover:border-gray-200"
        >
          <span class="text-sm font-medium text-gray-900">{{ m.label }}</span>
          <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
