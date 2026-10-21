<script setup>
import { computed, onErrorCaptured, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import BottomNav from '@/components/layout/BottomNav.vue'

const route = useRoute()
const routeError = ref(false)
const showBottomNav = computed(() => route.meta.tab !== false)

onErrorCaptured(() => {
  routeError.value = true
  return false
})

watch(
  () => route.path,
  () => {
    routeError.value = false
  },
)

function reload() {
  window.location.reload()
}
</script>

<template>
  <div class="mx-auto min-h-screen w-full max-w-app bg-gray-50 shadow-[0_0_0_1px_rgba(0,0,0,0.04)]">
    <div v-if="routeError" class="card m-5 p-6 text-center">
      <p class="text-sm font-medium text-gray-900">页面加载出错了</p>
      <p class="mt-1 text-xs text-gray-500">可能是网络或缓存问题，重新加载通常可以恢复。</p>
      <button
        type="button"
        class="mt-4 rounded-2xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white"
        @click="reload"
      >
        重新加载
      </button>
    </div>
    <main v-else :class="showBottomNav ? 'pb-[calc(3.5rem+env(safe-area-inset-bottom))]' : ''">
      <router-view />
    </main>
    <BottomNav v-if="showBottomNav" />
  </div>
</template>
