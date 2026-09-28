<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { createEvaluation, getEvaluation } from '@/api/interview'
import { extractInterviewError, needsModelConfig } from '@/utils/interview'
import { getKnowledgeCategoryLabel } from '@/utils/knowledge'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.sessionId

// loading：初始 GET；generating：触发 POST；completed / failed / error
const status = ref('loading')
const report = ref(null)
const failedError = ref('')
const error = ref('')
const errorCode = ref('')
const expanded = ref({})

function scoreLabel(score) {
  if (score >= 90) return '表现优秀'
  if (score >= 75) return '表现良好'
  if (score >= 60) return '基础合格'
  if (score >= 40) return '需要加强'
  return '需要重点提升'
}

function friendlyMessage(code, fallback) {
  const map = {
    INTERVIEW_SESSION_NOT_FOUND: '找不到这场面试',
    INTERVIEW_INVALID_STATE: '这场面试还没有完成，暂时无法生成评价。',
    INTERVIEW_MODEL_NOT_FOUND: '请先配置支持面试评价的 AI 模型',
  }
  return map[code] || fallback
}

function toggleDimension(name) {
  expanded.value = { ...expanded.value, [name]: !expanded.value[name] }
}

async function generate() {
  status.value = 'generating'
  error.value = ''
  errorCode.value = ''
  failedError.value = ''
  try {
    report.value = await createEvaluation(sessionId)
    status.value = 'completed'
  } catch (e) {
    const { code, message } = extractInterviewError(e)
    if (code === 'EVALUATION_FAILED') {
      failedError.value = message
      status.value = 'failed'
    } else {
      errorCode.value = code
      error.value = message
      status.value = 'error'
    }
  }
}

async function load() {
  status.value = 'loading'
  try {
    const data = await getEvaluation(sessionId)
    if (data.status === 'completed') {
      report.value = data
      status.value = 'completed'
    } else {
      failedError.value = data.error || '评价生成失败'
      status.value = 'failed'
    }
  } catch (e) {
    const { code, message } = extractInterviewError(e)
    if (code === 'EVALUATION_NOT_FOUND') {
      await generate()
      return
    }
    errorCode.value = code
    error.value = message
    status.value = 'error'
  }
}

onMounted(load)
</script>

<template>
  <div class="min-h-[100dvh]">
    <PageHeader title="AI 面试评价" />

    <!-- 加载 / 生成中 -->
    <div
      v-if="status === 'loading' || status === 'generating'"
      class="flex flex-col items-center justify-center px-8 py-28 text-center"
    >
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-brand-600"></div>
      <p class="mt-4 text-sm font-medium text-gray-900">正在分析你的面试表现</p>
      <p class="mt-1 text-xs text-gray-400">AI 正在根据你的回答、追问和评价标准生成报告</p>
    </div>

    <!-- 错误 -->
    <div v-else-if="status === 'error'" class="flex flex-col items-center justify-center px-6 py-28 text-center">
      <p class="text-sm text-gray-500">{{ friendlyMessage(errorCode, error) }}</p>
      <div class="mt-5 flex gap-3">
        <button
          v-if="needsModelConfig(errorCode)"
          type="button"
          class="rounded-2xl bg-brand-600 px-5 py-3 text-sm font-medium text-white active:bg-brand-700"
          @click="router.push('/profile/ai-models')"
        >
          去配置模型
        </button>
        <button
          type="button"
          class="rounded-2xl border border-gray-200 px-5 py-3 text-sm text-gray-600 active:bg-gray-50"
          @click="router.push('/interview/setup')"
        >
          返回面试设置
        </button>
      </div>
    </div>

    <!-- 生成失败 -->
    <div v-else-if="status === 'failed'" class="flex flex-col items-center justify-center px-6 py-28 text-center">
      <p class="text-sm font-medium text-gray-900">评价生成失败</p>
      <p class="mt-2 text-xs text-gray-400">{{ failedError }}</p>
      <div class="mt-6 w-full max-w-xs">
        <PrimaryButton @click="generate">重新生成</PrimaryButton>
      </div>
      <button
        type="button"
        class="mt-3 text-sm text-gray-500"
        @click="router.push('/interview/setup')"
      >
        返回面试设置
      </button>
    </div>

    <!-- 报告 -->
    <div v-else class="px-5 py-6">
      <section class="text-center">
        <p class="text-sm font-semibold text-gray-900">综合表现</p>
        <p class="mt-1 text-xs text-gray-400">{{ report.direction }} · {{ report.difficulty }}</p>
        <p class="mt-6 text-6xl font-bold leading-none text-brand-600">{{ report.overall_score }}</p>
        <p class="mt-3 text-sm text-gray-500">综合评分</p>
        <p class="mt-1 text-xs text-gray-400">{{ scoreLabel(report.overall_score) }}</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="能力分析" />
        <div class="mt-3 space-y-2">
          <div v-for="d in report.dimensions" :key="d.dimension" class="card rounded-2xl">
            <button type="button" class="w-full p-4 text-left" @click="toggleDimension(d.dimension)">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-900">{{ d.dimension }}</span>
                <span class="text-sm font-semibold text-gray-900">{{ d.score }}</span>
              </div>
              <ProgressBar :value="d.score" size="sm" class="mt-2" />
            </button>
            <div v-if="expanded[d.dimension]" class="border-t border-gray-100 px-4 py-3">
              <div v-if="d.strengths.length">
                <p class="text-xs font-medium text-gray-400">优势</p>
                <ul class="mt-1 space-y-1 text-sm text-gray-600">
                  <li v-for="s in d.strengths" :key="s">· {{ s }}</li>
                </ul>
              </div>
              <div v-if="d.weaknesses.length" class="mt-3">
                <p class="text-xs font-medium text-gray-400">问题</p>
                <ul class="mt-1 space-y-1 text-sm text-gray-600">
                  <li v-for="w in d.weaknesses" :key="w">· {{ w }}</li>
                </ul>
              </div>
              <div v-if="d.evidence.length" class="mt-3">
                <p class="text-xs font-medium text-gray-400">评价依据</p>
                <ul class="mt-1 space-y-1 text-sm text-gray-500">
                  <li v-for="(ev, i) in d.evidence" :key="i">· {{ ev.observation }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="mt-8">
        <SectionTitle title="表现不错的地方" />
        <ul v-if="report.overall_strengths.length" class="mt-2 space-y-2 text-sm text-gray-600">
          <li v-for="s in report.overall_strengths" :key="s" class="flex items-start gap-2">
            <svg class="mt-0.5 h-4 w-4 shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <span>{{ s }}</span>
          </li>
        </ul>
        <p v-else class="mt-2 text-sm text-gray-400">本次面试没有提取到明显优势。</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="需要提升" />
        <ul v-if="report.overall_weaknesses.length" class="mt-2 space-y-2 text-sm text-gray-600">
          <li v-for="w in report.overall_weaknesses" :key="w" class="flex items-start gap-2">
            <svg class="mt-0.5 h-4 w-4 shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 2.874 1.448 2.874h15.71c1.23 0 2.314-1.374 1.448-2.874L13.448 3.376a1.5 1.5 0 00-2.896 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
            </svg>
            <span>{{ w }}</span>
          </li>
        </ul>
        <p v-else class="mt-2 text-sm text-gray-400">本次面试没有发现明显短板。</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="AI 面试总结" />
        <p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-600">{{ report.summary }}</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="推荐学习" />
        <div v-if="report.recommended_knowledge.length" class="mt-3 space-y-2">
          <RouterLink
            v-for="k in report.recommended_knowledge"
            :key="k.knowledge_id"
            :to="`/learning/knowledge/${k.knowledge_id}`"
            class="card flex items-center justify-between p-4 transition-colors hover:border-gray-200"
          >
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-900">{{ k.title }}</p>
              <p class="mt-0.5 text-xs text-gray-400">{{ getKnowledgeCategoryLabel(k.category) }}</p>
              <p v-if="k.reason" class="mt-1 text-xs leading-relaxed text-gray-500">{{ k.reason }}</p>
            </div>
            <svg class="ml-3 h-4 w-4 shrink-0 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </RouterLink>
        </div>
        <p v-else class="mt-2 text-sm text-gray-400">暂无推荐学习内容。</p>
      </section>

      <div class="mt-8">
        <PrimaryButton @click="router.push('/interview/setup')">再来一次面试</PrimaryButton>
      </div>
    </div>
  </div>
</template>
