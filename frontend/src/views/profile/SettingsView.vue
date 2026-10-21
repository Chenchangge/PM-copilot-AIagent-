<script setup>
import { ref } from 'vue'

import PageHeader from '@/components/layout/PageHeader.vue'
import { reindexKnowledge } from '@/api/knowledge'
import { extractInterviewError } from '@/utils/interview'

const settings = [
  { label: '外观', value: '浅色' },
  { label: '关于 PM Copilot', value: 'v0.1.0' },
]

const rebuilding = ref(false)
const reindexMessage = ref('')
const reindexError = ref('')

async function rebuildIndex() {
  if (rebuilding.value) return
  rebuilding.value = true
  reindexMessage.value = ''
  reindexError.value = ''
  try {
    const data = await reindexKnowledge()
    reindexMessage.value = `索引已重建：${data.documents} 篇 / ${data.chunks} 段（${data.embedding_model}）`
  } catch (e) {
    reindexError.value = extractInterviewError(e).message
  } finally {
    rebuilding.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="设置" />
    <div class="px-5 py-4">
      <div class="overflow-hidden rounded-2xl border border-gray-100 bg-white">
        <div
          v-for="(s, i) in settings"
          :key="s.label"
          class="flex items-center justify-between px-4 py-3.5"
          :class="i > 0 ? 'border-t border-gray-50' : ''"
        >
          <span class="text-sm text-gray-900">{{ s.label }}</span>
          <span class="text-sm text-gray-500">{{ s.value }}</span>
        </div>
      </div>

      <section class="card mt-5 p-4">
        <p class="text-sm font-semibold text-gray-900">知识库索引</p>
        <p class="mt-1 text-xs leading-relaxed text-gray-500">
          知识库内容更新，或更换 Embedding 模型后，需要重建索引，否则问答可能检索不到新内容。
        </p>
        <button
          type="button"
          class="mt-3 rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 disabled:text-gray-400"
          :disabled="rebuilding"
          @click="rebuildIndex"
        >
          {{ rebuilding ? '重建中…' : '重建知识库索引' }}
        </button>
        <p v-if="reindexMessage" class="mt-2 text-xs text-green-600">{{ reindexMessage }}</p>
        <p v-if="reindexError" class="mt-2 text-xs text-red-500">{{ reindexError }}</p>
      </section>

      <p class="mt-4 text-xs text-gray-500">
        API Key 仅在后端保存，前端不存储任何密钥。
      </p>
    </div>
  </div>
</template>
