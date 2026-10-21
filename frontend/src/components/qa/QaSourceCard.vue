<script setup>
import { RouterLink } from 'vue-router'

import { getKnowledgeCategoryLabel } from '@/utils/knowledge'

defineProps({
  source: { type: Object, required: true }, // { knowledge_id, title, section, category, ... }
  to: { type: String, default: '' }, // 可跳转时的知识详情路由；空则不可点击
})
</script>

<template>
  <component
    :is="to ? RouterLink : 'div'"
    :to="to || undefined"
    class="block rounded-xl border border-gray-100 bg-white px-3 py-2 transition-colors"
    :class="to ? 'active:bg-gray-50' : ''"
  >
    <p class="truncate text-xs font-medium text-gray-900">{{ source.title }}</p>
    <p class="mt-0.5 truncate text-xs text-gray-400">
      {{ [source.section, getKnowledgeCategoryLabel(source.category)].filter(Boolean).join(' · ') || '知识库' }}
    </p>
    <p v-if="source.extra_chunks" class="mt-0.5 text-[11px] text-gray-400">
      该文另有 {{ source.extra_chunks }} 段相关
    </p>
  </component>
</template>
