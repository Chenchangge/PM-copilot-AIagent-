<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import ChatMessage from '@/components/ui/ChatMessage.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { qaPresets } from '@/mock'

const router = useRouter()
const input = ref('')
const messages = ref([])

function send(text) {
  const q = (text || input.value).trim()
  if (!q) return
  messages.value.push({ id: Date.now(), role: 'user', text: q })
  const preset = qaPresets.find((p) => p.q === q)
  messages.value.push({
    id: Date.now() + 1,
    role: 'ai',
    text: preset ? preset.a : '这是一个 Mock 回答，真实 AI 将在后续阶段接入 DeepSeek 与知识库检索。',
    references: preset ? preset.refs : [],
  })
  input.value = ''
}
</script>

<template>
  <div class="flex h-[calc(100dvh-3.5rem-env(safe-area-inset-bottom))] flex-col">
    <header class="flex shrink-0 items-center gap-1 border-b border-gray-100 bg-white/95 px-3 py-2.5">
      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-full text-gray-600 hover:bg-gray-100"
        aria-label="返回"
        @click="router.back()"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
      </button>
      <div>
        <p class="text-sm font-semibold text-gray-900">AI 产品学习助手</p>
        <p class="text-xs text-gray-400">基于 PM Copilot 知识库回答</p>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto px-5 py-4">
      <EmptyState
        v-if="!messages.length"
        title="问我产品经理知识"
        description="试着问「什么是 RAG？」或「什么是 MVP？」"
      >
        <template #action>
          <div class="flex flex-wrap justify-center gap-2">
            <button
              v-for="p in qaPresets"
              :key="p.q"
              type="button"
              class="rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-xs text-gray-600 active:bg-gray-50"
              @click="send(p.q)"
            >
              {{ p.q }}
            </button>
          </div>
        </template>
      </EmptyState>

      <div v-else class="space-y-3">
        <ChatMessage v-for="m in messages" :key="m.id" :role="m.role" :references="m.references">
          {{ m.text }}
        </ChatMessage>
      </div>
    </div>

    <div class="shrink-0 border-t border-gray-100 bg-white px-4 py-3">
      <div class="flex items-center gap-2">
        <input
          v-model="input"
          type="text"
          placeholder="输入你的问题…"
          class="flex-1 rounded-full border border-gray-200 bg-white px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none"
          @keyup.enter="send()"
        />
        <button
          type="button"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white transition-colors hover:bg-brand-700 active:bg-brand-700"
          aria-label="发送"
          @click="send()"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
