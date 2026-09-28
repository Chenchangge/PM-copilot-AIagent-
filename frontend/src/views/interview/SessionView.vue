<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { finishInterviewSession, getInterviewSession, submitInterviewAnswer } from '@/api/interview'
import { extractInterviewError, needsModelConfig } from '@/utils/interview'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id

const session = ref(null)
const turns = ref([])
const answer = ref('')
const loading = ref(true) // 初始加载
const submitting = ref(false)
const finishing = ref(false)
const showFinishConfirm = ref(false)
const error = ref('')
const errorCode = ref('')
const pendingRequestId = ref(null)
const scrollRef = ref(null)

const completed = computed(() => session.value?.status === 'completed')
const totalMain = computed(() => session.value?.max_main_questions || 5)
const progressLabel = computed(() => {
  const s = session.value
  return s ? `第 ${s.current_round} / ${totalMain.value} 题` : ''
})
const configLabel = computed(() => {
  const s = session.value
  return s ? `${s.direction} · ${s.difficulty}` : ''
})

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function load() {
  try {
    const data = await getInterviewSession(sessionId)
    session.value = data.session
    turns.value = data.turns || []
  } catch (e) {
    const { code, message } = extractInterviewError(e)
    errorCode.value = code
    error.value = message
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function submit() {
  const text = answer.value.trim()
  if (!text || submitting.value || completed.value) return
  submitting.value = true
  error.value = ''
  errorCode.value = ''
  // 生成一次 request id；网络失败重试时复用，避免后端重复落库 / 重复调用 LLM
  if (!pendingRequestId.value) {
    pendingRequestId.value = `${Date.now()}-${Math.random().toString(36).slice(2)}`
  }
  try {
    await submitInterviewAnswer(sessionId, { answer: text, client_request_id: pendingRequestId.value })
    answer.value = ''
    pendingRequestId.value = null
    await load()
  } catch (e) {
    const { code, message } = extractInterviewError(e)
    errorCode.value = code
    error.value = message
    // 保留 answer 与 pendingRequestId，供用户重试
  } finally {
    submitting.value = false
  }
}

async function confirmFinish() {
  if (finishing.value) return
  finishing.value = true
  error.value = ''
  errorCode.value = ''
  try {
    await finishInterviewSession(sessionId)
    showFinishConfirm.value = false
    await load()
  } catch (e) {
    const { code, message } = extractInterviewError(e)
    errorCode.value = code
    error.value = message
  } finally {
    finishing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="flex h-[calc(100dvh-3.5rem-env(safe-area-inset-bottom))] flex-col">
    <PageHeader title="AI 面试" />

    <!-- 初始加载 -->
    <div v-if="loading" class="flex flex-1 items-center justify-center text-sm text-gray-400">加载中…</div>

    <!-- 加载失败（无任何数据） -->
    <div v-else-if="error && !turns.length" class="flex flex-1 flex-col items-center justify-center px-6">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="router.push('/interview/setup')">返回面试设置</button>
    </div>

    <template v-else>
      <!-- 对话区 -->
      <div ref="scrollRef" class="flex-1 overflow-y-auto px-4 py-4">
        <div class="flex items-center justify-between text-xs text-gray-500">
          <span>{{ configLabel }}</span>
          <span class="font-medium text-brand-600">{{ progressLabel }}</span>
        </div>

        <div class="mt-4 space-y-3">
          <template v-for="t in turns" :key="t.turn_id">
            <div class="card rounded-2xl p-4">
              <p class="text-xs font-medium" :class="t.type === 'follow_up' ? 'text-brand-600' : 'text-gray-500'">
                {{ t.type === 'follow_up' ? '追问' : '问题' }}
              </p>
              <p class="mt-1 whitespace-pre-wrap break-words text-sm font-medium leading-relaxed text-gray-900">{{ t.question_content }}</p>
            </div>
            <div v-if="t.answer_content" class="flex justify-end">
              <div class="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-sm leading-relaxed text-white">
                {{ t.answer_content }}
              </div>
            </div>
          </template>

          <!-- AI 分析中 -->
          <div v-if="submitting" class="flex justify-start">
            <div class="card rounded-bl-md px-4 py-2.5 text-sm text-gray-400">AI 面试官正在分析你的回答…</div>
          </div>

          <!-- 完成提示 -->
          <div v-if="completed" class="card mt-6 rounded-2xl p-5 text-center">
            <p class="text-sm font-semibold text-gray-900">本次模拟面试已完成</p>
            <p class="mt-1 text-xs text-gray-400">可以查看你的 AI 面试评价报告了。</p>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div v-if="!completed" class="shrink-0 border-t border-gray-100 bg-white px-4 py-3">
        <div v-if="error" class="mb-2 flex items-center gap-2">
          <p class="flex-1 text-xs text-red-500">{{ error }}</p>
          <button
            v-if="needsModelConfig(errorCode)"
            type="button"
            class="shrink-0 text-xs font-medium text-brand-600"
            @click="router.push('/profile/ai-models')"
          >
            去配置模型
          </button>
        </div>
        <textarea
          v-model="answer"
          rows="3"
          placeholder="输入你的回答…"
          class="max-h-[160px] w-full resize-none rounded-2xl border border-gray-200 bg-white p-3 text-sm leading-relaxed focus:border-brand-500 focus:outline-none"
        ></textarea>
        <div class="mt-2 flex gap-2">
          <button
            type="button"
            class="shrink-0 rounded-2xl border border-gray-200 px-4 py-3 text-sm text-gray-600 active:bg-gray-50"
            @click="showFinishConfirm = true"
          >
            结束面试
          </button>
          <div class="flex-1">
            <PrimaryButton :disabled="submitting || !answer.trim()" @click="submit">
              {{ submitting ? '分析中…' : '提交回答' }}
            </PrimaryButton>
          </div>
        </div>
      </div>

      <!-- 完成态操作 -->
      <div v-else class="shrink-0 space-y-2 border-t border-gray-100 bg-white px-5 py-3">
        <PrimaryButton @click="router.push(`/interview/${sessionId}/evaluation`)">查看面试评价</PrimaryButton>
        <button
          type="button"
          class="w-full rounded-2xl border border-gray-200 py-3.5 text-sm text-gray-600 active:bg-gray-50"
          @click="router.push('/interview/setup')"
        >
          再来一次面试
        </button>
      </div>
    </template>

    <!-- 结束确认弹窗 -->
    <div v-if="showFinishConfirm" class="fixed inset-0 z-40 flex items-center justify-center px-6">
      <div class="absolute inset-0 bg-black/40" @click="showFinishConfirm = false"></div>
      <div class="relative w-full max-w-sm rounded-2xl bg-white p-5">
        <p class="text-base font-semibold text-gray-900">确定要结束本次面试吗？</p>
        <p class="mt-2 text-sm text-gray-500">结束后将无法继续回答当前问题。</p>
        <div class="mt-5 flex gap-3">
          <button
            type="button"
            class="flex-1 rounded-2xl border border-gray-200 py-3 text-sm text-gray-600 active:bg-gray-50"
            @click="showFinishConfirm = false"
          >
            继续面试
          </button>
          <button
            type="button"
            class="flex-1 rounded-2xl bg-red-500 py-3 text-sm font-medium text-white disabled:bg-red-300"
            :disabled="finishing"
            @click="confirmFinish"
          >
            {{ finishing ? '结束中…' : '结束面试' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
