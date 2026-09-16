<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  size: { type: String, default: 'md' }, // 'sm' | 'md'
})

const width = computed(() => `${Math.min(Math.max(props.value, 0), 100)}%`)
</script>

<template>
  <div class="w-full overflow-hidden rounded-full bg-gray-100" :class="size === 'sm' ? 'h-1.5' : 'h-2'">
    <div class="h-full rounded-full bg-brand-600 transition-all" :style="{ width }" />
  </div>
</template>
