<script setup>
import { computed, onErrorCaptured, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import BottomNav from '@/components/layout/BottomNav.vue'
import DesktopNav from '@/components/layout/DesktopNav.vue'

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
  <div class="mx-auto min-h-screen w-full max-w-app bg-gray-50 shadow-[0_0_0_1px_rgba(0,0,0,0.04)] lg:flex lg:max-w-[960px] lg:gap-6 lg:px-6 lg:py-6 lg:shadow-none">
    <DesktopNav />
    <div class="min-w-0 flex-1">
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
      <main v-else :class="showBottomNav ? 'pb-[calc(3.5rem+env(safe-area-inset-bottom))] lg:pb-0' : ''">
        <router-view />
      </main>
    </div>
    <BottomNav v-if="showBottomNav" class="lg:hidden" />
  </div>
</template>
