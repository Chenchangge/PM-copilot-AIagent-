<script setup>
import { computed, ref } from 'vue'

import LearningTabs from '@/components/learning/LearningTabs.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import KnowledgeItem from '@/components/ui/KnowledgeItem.vue'
import { knowledgeCategories, knowledgeList } from '@/mock'

const active = ref('全部')
const keyword = ref('')
const categories = ['全部', ...knowledgeCategories]

const filtered = computed(() => {
  const kw = keyword.value.trim()
  const list = active.value === '全部' ? knowledgeList : knowledgeList.filter((k) => k.category === active.value)
  if (!kw) return list
  return list.filter((k) => k.title.includes(kw) || k.summary.includes(kw))
})
</script>

<template>
  <div>
    <div class="px-5 pt-5">
      <h1 class="text-xl font-bold text-gray-900">学习</h1>
    </div>

    <LearningTabs />

    <div class="px-5 py-4">
      <div class="relative">
        <svg class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索产品知识"
          class="w-full rounded-full border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-brand-500 focus:outline-none"
        />
      </div>

      <div class="mt-4 flex gap-2 overflow-x-auto pb-1">
        <button
          v-for="c in categories"
          :key="c"
          type="button"
          class="shrink-0 rounded-full border px-4 py-1.5 text-sm transition-colors"
          :class="active === c ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
          @click="active = c"
        >
          {{ c }}
        </button>
      </div>

      <div v-if="filtered.length" class="mt-4 space-y-3">
        <KnowledgeItem v-for="k in filtered" :key="k.id" :item="k" :to="`/learning/knowledge/${k.id}`" />
      </div>
      <EmptyState v-else title="没有找到相关知识" description="换个关键词或分类试试" />
    </div>
  </div>
</template>
