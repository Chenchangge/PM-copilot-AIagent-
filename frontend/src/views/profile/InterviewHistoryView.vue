<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { interviewHistory } from '@/mock'
</script>

<template>
  <div>
    <PageHeader title="面试记录" />
    <div class="px-5 py-4">
      <div v-if="interviewHistory.length" class="space-y-2">
        <RouterLink
          v-for="h in interviewHistory"
          :key="h.id"
          :to="`/interview/report/${h.id}`"
          class="card flex items-center justify-between p-4 transition-colors hover:border-gray-200"
        >
          <div>
            <p class="text-sm font-medium text-gray-900">{{ h.direction }} · {{ h.type }}</p>
            <p class="mt-1 text-xs text-gray-400">{{ h.date }}</p>
          </div>
          <span class="text-lg font-bold text-brand-600">{{ h.score }}</span>
        </RouterLink>
      </div>
      <EmptyState v-else title="暂无面试记录" description="去完成一次模拟面试吧" />
    </div>
  </div>
</template>
