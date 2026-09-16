<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  {
    name: '首页',
    section: 'home',
    path: '/home',
    icon: 'M2.25 12l8.954-8.955a1.126 1.126 0 011.592 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75',
  },
  {
    name: '学习',
    section: 'learning',
    path: '/learning/knowledge',
    icon: 'M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25',
  },
  {
    name: '面试',
    section: 'interview',
    path: '/interview/setup',
    icon: 'M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z',
  },
  {
    name: '我的',
    section: 'profile',
    path: '/profile',
    icon: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z',
  },
]

function isActive(tab) {
  if (tab.section === 'home') return route.path === '/home'
  return route.path.startsWith(`/${tab.section}`)
}
</script>

<template>
  <nav
    class="fixed bottom-0 left-1/2 z-20 w-full max-w-app -translate-x-1/2 border-t border-gray-100 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur"
  >
    <div class="grid h-14 grid-cols-4">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.section"
        :to="tab.path"
        class="flex flex-col items-center justify-center gap-0.5 text-xs"
        :class="isActive(tab) ? 'text-brand-600' : 'text-gray-400'"
      >
        <svg
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.6"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" :d="tab.icon" />
        </svg>
        {{ tab.name }}
      </RouterLink>
    </div>
  </nav>
</template>
