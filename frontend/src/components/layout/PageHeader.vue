<script setup>
import { useRouter } from 'vue-router'

defineProps({
  title: { type: String, default: '' },
  back: { type: Boolean, default: true },
})

const router = useRouter()
</script>

<template>
  <header
    class="sticky top-0 z-10 flex h-14 items-center gap-1 border-b border-gray-100 bg-white/80 px-3 backdrop-blur"
  >
    <button
      v-if="back"
      type="button"
      class="flex h-9 w-9 items-center justify-center rounded-full text-gray-600 hover:bg-gray-100"
      aria-label="返回"
      @click="router.back()"
    >
      <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
      </svg>
    </button>
    <h1 class="text-base font-semibold text-gray-900" :class="back ? '' : 'ml-2'">{{ title }}</h1>
  </header>
</template>
