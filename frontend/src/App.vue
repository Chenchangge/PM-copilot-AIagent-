<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import BottomNav from '@/components/layout/BottomNav.vue'

const route = useRoute()
const showBottomNav = computed(() => route.meta.tab !== false)
</script>

<template>
  <div class="mx-auto min-h-screen w-full max-w-app bg-gray-50 shadow-[0_0_0_1px_rgba(0,0,0,0.04)]">
    <main :class="showBottomNav ? 'pb-[calc(3.5rem+env(safe-area-inset-bottom))]' : ''">
      <router-view />
    </main>
    <BottomNav v-if="showBottomNav" />
  </div>
</template>
