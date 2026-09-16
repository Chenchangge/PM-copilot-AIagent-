<script setup>
defineProps({
  item: { type: Object, required: true },
  to: { type: String, required: true },
})

function statusClass(status) {
  if (status === '已完成') return 'text-green-600'
  if (status === '进行中') return 'text-brand-600'
  return 'text-gray-400'
}
</script>

<template>
  <RouterLink :to="to" class="card block p-4 transition-colors hover:border-gray-200">
    <div class="flex items-center justify-between">
      <p class="text-xs font-medium text-brand-600">{{ item.category }}</p>
      <span v-if="item.status" class="text-xs" :class="statusClass(item.status)">{{ item.status }}</span>
    </div>
    <h3 class="mt-1 text-sm font-medium text-gray-900">{{ item.title }}</h3>
    <p v-if="item.summary" class="mt-1 text-sm text-gray-500 line-clamp-2">{{ item.summary }}</p>
    <div v-if="item.readMinutes || item.updatedAt" class="mt-2 flex items-center gap-3 text-xs text-gray-400">
      <span v-if="item.readMinutes">{{ item.readMinutes }} 分钟</span>
      <span v-if="item.updatedAt">{{ item.updatedAt }}</span>
    </div>
  </RouterLink>
</template>
