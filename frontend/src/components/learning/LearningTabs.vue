<script setup>
import { useRoute } from 'vue-router'

const tabs = [
  { label: '知识库', to: '/learning/knowledge' },
  { label: '知识问答', to: '/learning/qa' },
  { label: '学习计划', to: '/learning/plan' },
]

const route = useRoute()

function isActive(tab) {
  if (tab.to === '/learning/knowledge') return route.path === '/learning/knowledge'
  return route.path.startsWith(tab.to)
}
</script>

<template>
  <div class="sticky top-0 z-10 border-b border-gray-100 bg-white/95 backdrop-blur">
    <div class="flex px-4">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        class="-mb-px border-b-2 px-3 py-3 text-sm"
        :class="isActive(tab) ? 'border-brand-600 font-medium text-brand-600' : 'border-transparent text-gray-500'"
      >
        {{ tab.label }}
      </RouterLink>
    </div>
  </div>
</template>
