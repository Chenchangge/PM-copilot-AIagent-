<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { name: '首页', section: 'home', path: '/home' },
  { name: '学习', section: 'learning', path: '/learning/knowledge' },
  { name: '模拟面试', section: 'interview', path: '/interview/setup' },
  { name: '我的', section: 'profile', path: '/profile' },
]

function isActive(tab) {
  if (tab.section === 'home') return route.path === '/home'
  return route.path.startsWith(`/${tab.section}`)
}
</script>

<template>
  <aside class="hidden w-44 shrink-0 lg:block">
    <div class="sticky top-6 rounded-2xl border border-gray-100 bg-white p-3">
      <div class="flex items-center gap-2 px-2 py-2">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">P</span>
        <span class="text-sm font-bold text-gray-900">PM Copilot</span>
      </div>
      <nav class="mt-3 space-y-1">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.section"
          :to="tab.path"
          class="flex items-center justify-between rounded-xl px-3 py-2.5 text-sm transition-colors"
          :class="isActive(tab) ? 'bg-brand-50 font-medium text-brand-700' : 'text-gray-600 hover:bg-gray-50'"
        >
          <span>{{ tab.name }}</span>
          <span v-if="isActive(tab)" class="h-1.5 w-1.5 rounded-full bg-brand-600"></span>
        </RouterLink>
      </nav>
    </div>
  </aside>
</template>
