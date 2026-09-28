<script setup>
import QaSourceCard from './QaSourceCard.vue'
import { sourceDetailPath } from '@/utils/knowledge'

defineProps({
  message: { type: Object, required: true },
})
const emit = defineEmits(['retry', 'go-models'])
</script>

<template>
  <div class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
    <div
      class="max-w-[85%] px-4 py-2.5 text-sm leading-relaxed"
      :class="message.role === 'user' ? 'rounded-2xl rounded-br-md bg-brand-600 text-white' : 'card rounded-bl-md'"
    >
      <!-- 用户消息 -->
      <p v-if="message.role === 'user'" class="whitespace-pre-wrap break-words">{{ message.content }}</p>

      <!-- 检索 + 生成中 -->
      <div v-else-if="message.loading" class="flex items-center gap-2 text-gray-400">
        <span
          class="h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-brand-100 border-t-brand-500"
        ></span>
        <span>正在检索知识并生成回答…</span>
      </div>

      <!-- 失败：友好错误 + 操作 -->
      <template v-else-if="message.error">
        <p class="text-gray-600">{{ message.error.message }}</p>
        <div class="mt-2.5 flex flex-wrap gap-2">
          <button
            v-if="message.error.needsModelConfig"
            type="button"
            class="rounded-full border border-brand-200 px-3 py-1 text-xs font-medium text-brand-600 active:bg-brand-50"
            @click="emit('go-models')"
          >
            去配置模型
          </button>
          <button
            type="button"
            class="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-600 active:bg-gray-50"
            @click="emit('retry')"
          >
            重试
          </button>
        </div>
      </template>

      <!-- 正常回答 -->
      <template v-else>
        <p class="whitespace-pre-wrap break-words text-gray-800">{{ message.content }}</p>

        <div v-if="message.sources && message.sources.length" class="mt-3 border-t border-gray-100 pt-2.5">
          <p class="text-xs text-gray-400">参考知识</p>
          <div class="mt-1.5 grid gap-1.5">
            <QaSourceCard
              v-for="(s, i) in message.sources"
              :key="s.chunk_id || i"
              :source="s"
              :to="sourceDetailPath(s)"
            />
          </div>
        </div>

        <p v-else-if="message.retrievalCount === 0" class="mt-2 text-xs text-gray-400">未找到相关知识来源</p>
      </template>
    </div>
  </div>
</template>
