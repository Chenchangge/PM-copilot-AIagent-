<script setup>
import { computed, onMounted, ref } from 'vue'
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
const expandedAnswers = ref({})

const turnMap = computed(() =>
  Object.fromEntries((report.value?.turn_reviews || []).map((t) => [t.turn_id, t])),
)

const POINT_STATUS = {
  met: { icon: '✓', class: 'bg-green-50 text-green-600' },
  partial: { icon: '△', class: 'bg-amber-50 text-amber-600' },
  missed: { icon: '✗', class: 'bg-red-50 text-red-500' },
  unknown: { icon: '—', class: 'bg-gray-100 text-gray-400' },
}

function pointMeta(status) {
  return POINT_STATUS[status] || POINT_STATUS.unknown
}

function turnTitle(turn) {
  return `第 ${turn.round_number} 题${turn.question_type === 'follow_up' ? ' · 追问' : ''}`
}

function evidenceLabel(evidence) {
  const turn = turnMap.value[evidence.turn_id]
  if (!turn) return `第 ${evidence.turn_id} 轮`
  return `第 ${turn.round_number} 题${turn.question_type === 'follow_up' ? ' · 追问' : ''}`
}

function toggleAnswer(turnId) {
  expandedAnswers.value = { ...expandedAnswers.value, [turnId]: !expandedAnswers.value[turnId] }
}

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

      <section v-if="report.turn_reviews && report.turn_reviews.length" class="mt-8">
        <SectionTitle title="逐题复盘" />
        <p class="mt-1 text-[11px] text-gray-400">✓ 达成 · △ 部分达成 · ✗ 未达成 · — 未判定</p>
        <div class="mt-3 space-y-2">
          <div v-for="t in report.turn_reviews" :key="t.turn_id" class="card rounded-2xl p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-xs font-medium text-brand-600">{{ turnTitle(t) }}</span>
                  <span v-if="t.question_type === 'follow_up' && t.follow_up_type" class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-500">{{ t.follow_up_type }}</span>
                </div>
                <p class="mt-1 text-sm font-medium leading-relaxed text-gray-900">{{ t.question }}</p>
              </div>
              <span
                v-if="t.score !== null && t.score !== undefined"
                class="shrink-0 rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-semibold text-brand-700"
              >
                {{ t.score }} 分
              </span>
              <span v-else class="shrink-0 text-[11px] text-gray-400">未单独评分</span>
            </div>

            <div v-if="t.answer" class="mt-3">
              <p class="text-[11px] text-gray-400">我的回答</p>
              <p
                class="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-gray-600"
                :class="expandedAnswers[t.turn_id] ? '' : 'line-clamp-3'"
              >
                {{ t.answer }}
              </p>
              <button
                v-if="t.answer.length > 90"
                type="button"
                class="mt-1 text-xs font-medium text-brand-600"
                @click="toggleAnswer(t.turn_id)"
              >
                {{ expandedAnswers[t.turn_id] ? '收起回答' : '展开回答' }}
              </button>
            </div>
            <p v-else class="mt-3 text-sm text-gray-400">未作答</p>

            <div v-if="t.point_results.length" class="mt-3">
              <p class="text-[11px] text-gray-400">评分点达成情况</p>
              <ul class="mt-1.5 space-y-1.5">
                <li v-for="(p, i) in t.point_results" :key="i" class="flex items-start gap-2 text-sm text-gray-600">
                  <span
                    class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold"
                    :class="pointMeta(p.status).class"
                  >
                    {{ pointMeta(p.status).icon }}
                  </span>
                  <span class="min-w-0">
                    {{ p.point }}
                    <span v-if="p.comment" class="mt-0.5 block text-[11px] leading-relaxed text-gray-400">{{ p.comment }}</span>
                  </span>
                </li>
              </ul>
            </div>

            <p v-if="t.comment" class="mt-2 rounded-xl bg-gray-50 px-3 py-2 text-xs leading-relaxed text-gray-500">
              点评：{{ t.comment }}
            </p>

            <details v-if="t.reference_answer" class="mt-3 rounded-xl bg-gray-50">
              <summary class="cursor-pointer list-none px-3 py-2 text-xs font-medium text-brand-600">查看参考答案</summary>
              <p class="whitespace-pre-wrap border-t border-gray-100 px-3 py-2.5 text-sm leading-relaxed text-gray-600">{{ t.reference_answer }}</p>
            </details>
          </div>
        </div>
      </section>

      <section class="mt-8">
        <SectionTitle title="能力分析" />
        <div class="mt-3 space-y-2">
          <div v-for="d in report.dimensions" :key="d.dimension" class="card rounded-2xl">
            <button type="button" class="w-full p-4 text-left" @click="toggleDimension(d.dimension)">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-900">{{ d.dimension }}</span>
                <span v-if="d.score !== null" class="text-sm font-semibold text-gray-900">{{ d.score }}</span>
                <span v-else class="text-xs text-gray-400">本场未考察</span>
              </div>
              <ProgressBar v-if="d.score !== null" :value="d.score" size="sm" class="mt-2" />
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
                  <li v-for="(ev, i) in d.evidence" :key="i">
                    <span class="text-[11px] font-medium text-brand-600">针对{{ evidenceLabel(ev) }}</span>
                    <span class="ml-1">{{ ev.observation }}</span>
                  </li>
                </ul>
              </div>
              <p v-else class="mt-3 text-xs text-gray-400">本场未考察该维度。</p>
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
