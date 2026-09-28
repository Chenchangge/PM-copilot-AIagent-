<script setup>
import { getKnowledgeCategoryLabel, getKnowledgeDifficultyLabel, getKnowledgeTopicLabel } from '@/utils/knowledge'

defineProps({
  item: { type: Object, required: true },
  to: { type: String, required: true },
})
</script>

<template>
  <RouterLink :to="to" class="card block p-4 transition-colors hover:border-gray-200">
    <div class="flex items-center justify-between">
      <p class="text-xs font-medium text-brand-600">
        {{ getKnowledgeCategoryLabel(item.category) }}<span v-if="item.topic"> · {{ getKnowledgeTopicLabel(item.topic) }}</span>
      </p>
      <span v-if="item.difficulty" class="text-xs text-gray-400">{{ getKnowledgeDifficultyLabel(item.difficulty) }}</span>
    </div>
    <h3 class="mt-1 text-sm font-medium text-gray-900">{{ item.title }}</h3>
    <div v-if="item.tags && item.tags.length" class="mt-2 flex flex-wrap gap-1.5">
      <span v-for="t in item.tags" :key="t" class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">{{ t }}</span>
    </div>
  </RouterLink>
</template>
