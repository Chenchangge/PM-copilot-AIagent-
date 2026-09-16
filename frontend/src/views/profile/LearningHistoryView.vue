<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { learningHistory } from '@/mock'

function statusClass(status) {
  if (status === '已完成') return 'text-green-600'
  if (status === '进行中') return 'text-brand-600'
  return 'text-gray-400'
}
</script>

<template>
  <div>
    <PageHeader title="学习记录" />
    <div class="px-5 py-4">
      <div v-if="learningHistory.length" class="space-y-2">
        <div
          v-for="h in learningHistory"
          :key="h.id"
          class="card flex items-center justify-between p-4"
        >
          <div>
            <p class="text-sm font-medium text-gray-900">{{ h.title }}</p>
            <p class="mt-1 text-xs text-gray-400">{{ h.date }}</p>
          </div>
          <span class="text-xs" :class="statusClass(h.status)">{{ h.status }}</span>
        </div>
      </div>
      <EmptyState v-else title="暂无学习记录" description="去知识库开始学习吧" />
    </div>
  </div>
</template>
