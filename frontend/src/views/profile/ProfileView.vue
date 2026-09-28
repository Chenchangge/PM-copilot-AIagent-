<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'

const menu = [
  { label: '学习记录', to: '/profile/learning-history' },
  { label: '面试记录', to: '/profile/interview-history' },
  { label: 'AI 模型 / API', to: '/profile/ai-models' },
  { label: '设置', to: '/profile/settings' },
]
</script>

<template>
  <div>
    <PageHeader title="我的" :back="false" />
    <div class="px-5 py-6">
      <p class="text-sm text-gray-400">匿名使用 · 你的学习与面试数据保存在本地</p>

      <div class="mt-6 space-y-3">
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
