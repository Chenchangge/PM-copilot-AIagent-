<script setup>
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'

import QaMessage from '@/components/qa/QaMessage.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { askKnowledge } from '@/api/knowledge'
import { errorMessageFor, needsModelConfig } from '@/utils/knowledge'

const router = useRouter()

// 快捷问题（仅占位，点击后直接发送，不自动调用 API）
const QUICK_QUESTIONS = ['什么是 MVP？', '如何做用户需求分析？', '什么是 RICE？', 'RAG 是什么？']

const input = ref('')
const messages = ref([])
const loading = ref(false)
const composing = ref(false)
const scrollRef = ref(null)
const inputRef = ref(null)

let seq = 0
const nextId = () => `m${Date.now()}-${++seq}`

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function runQuery(msg) {
  loading.value = true
  try {
    const data = await askKnowledge({ query: msg.query })
    msg.content = data.answer || ''
    msg.sources = data.sources || []
    msg.retrievalCount = data.retrieval_count ?? 0
    msg.loading = false
    msg.error = null
  } catch (err) {
    const body = err?.response?.data
    const code = body?.error?.code || null
    const backendMessage = body?.error?.message || null
    msg.content = ''
    msg.loading = false
    msg.error = {
      code,
      message: errorMessageFor(code, backendMessage),
      needsModelConfig: needsModelConfig(code),
    }
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function send(text) {
  const q = (text ?? input.value).trim()
  if (!q || loading.value) return
  input.value = ''
  resetInputHeight()
  messages.value.push({ id: nextId(), role: 'user', content: q })
  messages.value.push({
    id: nextId(),
    role: 'assistant',
    content: '',
    sources: [],
    retrievalCount: 0,
    loading: true,
    error: null,
    query: q,
  })
  scrollToBottom()
  runQuery(messages.value[messages.value.length - 1])
}

function retry(msg) {
  if (loading.value) return
  msg.loading = true
  msg.error = null
  runQuery(msg)
}

function goModels() {
  router.push('/profile/ai-models')
}

// Enter 发送 / Shift+Enter 换行；中文输入法 composition 期间不误判发送。
function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !composing.value && !e.isComposing) {
    e.preventDefault()
    send()
  }
}

function onCompositionStart() {
  composing.value = true
}

function onCompositionEnd() {
  composing.value = false
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`
}

function resetInputHeight() {
  const el = inputRef.value
  if (el) el.style.height = 'auto'
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
        <p class="text-sm font-semibold text-gray-900">知识问答</p>
        <p class="text-xs text-gray-400">基于 PM Copilot 知识库回答</p>
      </div>
    </header>

    <div ref="scrollRef" class="flex-1 overflow-y-auto px-4 py-4">
      <EmptyState
        v-if="!messages.length"
        title="有什么产品经理知识想了解？"
        description="试着问一个产品问题，我会结合知识库回答。"
      >
        <template #action>
          <div class="flex flex-wrap justify-center gap-2">
            <button
              v-for="q in QUICK_QUESTIONS"
              :key="q"
              type="button"
              class="rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-xs text-gray-600 active:bg-gray-50"
              @click="send(q)"
            >
              {{ q }}
            </button>
          </div>
        </template>
      </EmptyState>

      <div v-else class="space-y-3">
        <QaMessage
          v-for="m in messages"
          :key="m.id"
          :message="m"
          @retry="retry(m)"
          @go-models="goModels"
        />
      </div>
    </div>

    <div class="shrink-0 border-t border-gray-100 bg-white px-4 py-3">
      <div class="flex items-end gap-2">
        <textarea
          ref="inputRef"
          v-model="input"
          rows="1"
          placeholder="输入你的问题…"
          class="max-h-[120px] flex-1 resize-none rounded-2xl border border-gray-200 bg-white px-4 py-2.5 text-sm leading-relaxed focus:border-brand-500 focus:outline-none"
          @keydown="onKeydown"
          @compositionstart="onCompositionStart"
          @compositionend="onCompositionEnd"
          @input="autoResize"
        ></textarea>
        <button
          type="button"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white transition-colors hover:bg-brand-700 active:bg-brand-700 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-400"
          :disabled="loading || !input.trim()"
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
