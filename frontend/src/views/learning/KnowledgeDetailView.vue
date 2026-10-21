<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { getKnowledgeDetail } from '@/api/knowledge'
import { completeKnowledge, completeTask, startKnowledge, startTask } from '@/api/learning'
import { getKnowledgeCategoryLabel, getKnowledgeDifficultyLabel, getKnowledgeTopicLabel } from '@/utils/knowledge'
import { extractInterviewError } from '@/utils/interview'
import { renderMarkdown } from '@/utils/markdown'

const route = useRoute()
const router = useRouter()
const knowledgeId = computed(() => route.params.id) // slug，如 mvp / rag-basics
const taskId = computed(() => route.query.taskId || null) // 从学习计划进入时携带

const detail = ref(null)
const loading = ref(true)
const error = ref('')

const learningStatus = ref('idle') // idle | started | completed
const learningBusy = ref(false)
const learningError = ref('')
const completedPlanId = ref(null)

const coreContentHtml = computed(() => renderMarkdown(detail.value?.core_content))

const RELATION_LABELS = {
  core: '核心题',
  related: '相关题',
  prerequisite: '前置知识关联',
}

function relationLabel(relation) {
  return RELATION_LABELS[relation] || '相关题'
}

async function load() {
  loading.value = true
  error.value = ''
  learningStatus.value = 'idle'
  learningError.value = ''
  completedPlanId.value = null
  try {
    detail.value = await getKnowledgeDetail(knowledgeId.value)
  } catch (e) {
    error.value = e?.response?.status === 404 ? '知识点不存在' : '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.id,
  () => load(),
)

async function start() {
  if (learningBusy.value) return
  learningBusy.value = true
  learningError.value = ''
  try {
    if (taskId.value) await startTask(taskId.value)
    else await startKnowledge(knowledgeId.value)
    learningStatus.value = 'started'
  } catch (e) {
    learningError.value = extractInterviewError(e).message
  } finally {
    learningBusy.value = false
  }
}

async function complete() {
  if (learningBusy.value) return
  learningBusy.value = true
  learningError.value = ''
  try {
    if (taskId.value) {
      const plan = await completeTask(taskId.value)
      completedPlanId.value = plan?.id || null
    } else {
      await completeKnowledge(knowledgeId.value)
    }
    learningStatus.value = 'completed'
  } catch (e) {
    learningError.value = extractInterviewError(e).message
  } finally {
    learningBusy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader :title="detail?.title || '知识详情'" />

    <div v-if="loading" class="px-5 py-20 text-center text-sm text-gray-400">加载中…</div>

    <div v-else-if="error" class="px-5 py-20 text-center">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="router.push('/learning/knowledge')">返回知识库</button>
    </div>

    <article v-else class="px-5 py-6">
      <div class="flex items-center gap-2 text-xs font-medium text-brand-600">
        <span>{{ getKnowledgeCategoryLabel(detail.category) }}</span>
        <span v-if="detail.topic" class="font-normal text-gray-500">· {{ getKnowledgeTopicLabel(detail.topic) }}</span>
        <span v-if="detail.difficulty" class="font-normal text-gray-400">· {{ getKnowledgeDifficultyLabel(detail.difficulty) }}</span>
      </div>

      <section class="mt-6">
        <SectionTitle title="知识定义" />
        <p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-600">{{ detail.definition }}</p>
      </section>

      <section v-if="detail.core_content" class="mt-8">
        <SectionTitle title="核心内容" />
        <div class="markdown-body mt-2 text-sm leading-relaxed text-gray-600" v-html="coreContentHtml"></div>
      </section>

      <!-- P0-2：核心内容之后依次端出库里已有的内容 -->
      <section v-if="detail.misconceptions.length" class="mt-8">
        <SectionTitle title="常见误区" />
        <ul class="mt-2 space-y-2 text-sm leading-relaxed text-gray-600">
          <li v-for="(item, i) in detail.misconceptions" :key="i" class="flex gap-2">
            <span class="mt-0.5 shrink-0 text-amber-500">×</span>
            <span>{{ item }}</span>
          </li>
        </ul>
      </section>

      <section v-if="detail.prerequisites.length" class="mt-8">
        <SectionTitle title="前置知识" />
        <div class="mt-2 space-y-2">
          <RouterLink
            v-for="p in detail.prerequisites"
            :key="p.id"
            :to="`/learning/knowledge/${p.id}`"
            class="card flex items-center justify-between gap-3 p-3.5 transition-colors hover:border-gray-200"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-gray-900">{{ p.title }}</p>
              <p class="mt-0.5 text-[11px] text-gray-400">
                {{ getKnowledgeCategoryLabel(p.category) }}
                <span v-if="p.topic"> · {{ getKnowledgeTopicLabel(p.topic) }}</span>
              </p>
            </div>
            <svg class="h-4 w-4 shrink-0 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </RouterLink>
        </div>
      </section>

      <section v-if="detail.related.length" class="mt-8">
        <SectionTitle title="相关知识点" />
        <div class="mt-2 space-y-2">
          <RouterLink
            v-for="p in detail.related"
            :key="p.id"
            :to="`/learning/knowledge/${p.id}`"
            class="card flex items-center justify-between gap-3 p-3.5 transition-colors hover:border-gray-200"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-gray-900">{{ p.title }}</p>
              <p class="mt-0.5 text-[11px] text-gray-400">
                {{ getKnowledgeCategoryLabel(p.category) }}
                <span v-if="p.topic"> · {{ getKnowledgeTopicLabel(p.topic) }}</span>
              </p>
            </div>
            <svg class="h-4 w-4 shrink-0 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </RouterLink>
        </div>
      </section>

      <section v-if="detail.related_questions.length" class="mt-8">
        <SectionTitle title="相关面试题" />
        <div class="mt-2 space-y-2">
          <details v-for="q in detail.related_questions" :key="q.id" class="card rounded-2xl">
            <summary class="flex cursor-pointer list-none items-start justify-between gap-3 p-4">
              <div class="min-w-0">
                <p class="text-sm font-medium leading-relaxed text-gray-900">{{ q.content }}</p>
                <div class="mt-1.5 flex flex-wrap items-center gap-1.5 text-[11px] text-gray-400">
                  <span class="rounded-full bg-brand-50 px-2 py-0.5 font-medium text-brand-700">{{ relationLabel(q.relation) }}</span>
                  <span v-if="q.difficulty">{{ getKnowledgeDifficultyLabel(q.difficulty) }}</span>
                  <span v-if="q.via_title">· 来自《{{ q.via_title }}》</span>
                </div>
              </div>
              <svg class="mt-0.5 h-4 w-4 shrink-0 text-gray-300 transition-transform" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </summary>
            <div v-if="q.reference_answer" class="border-t border-gray-100 px-4 py-3">
              <p class="text-[11px] text-gray-400">参考答案</p>
              <p class="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-gray-600">{{ q.reference_answer }}</p>
            </div>
          </details>
        </div>
      </section>

      <section v-if="detail.cases.length" class="mt-8">
        <SectionTitle title="案例" />
        <ul class="mt-2 space-y-2 text-sm leading-relaxed text-gray-600">
          <li v-for="(item, i) in detail.cases" :key="i" class="rounded-xl bg-gray-50 p-3">{{ item }}</li>
        </ul>
      </section>

      <section v-if="detail.common_scenarios.length" class="mt-8">
        <SectionTitle title="常见场景" />
        <ul class="mt-2 space-y-1.5 text-sm text-gray-600">
          <li v-for="(s, i) in detail.common_scenarios" :key="i">· {{ s }}</li>
        </ul>
      </section>

      <section v-if="detail.pm_focus.length" class="mt-8">
        <SectionTitle title="产品经理需要关注什么" />
        <ul class="mt-2 space-y-1.5 text-sm text-gray-600">
          <li v-for="(f, i) in detail.pm_focus" :key="i">· {{ f }}</li>
        </ul>
      </section>

      <section v-if="detail.interview_questions.length" class="mt-8">
        <SectionTitle title="常见面试问题" />
        <div class="mt-2 space-y-2">
          <details v-for="(q, i) in detail.interview_questions" :key="i" class="card rounded-2xl">
            <summary class="flex cursor-pointer list-none items-center justify-between p-4 text-sm font-medium text-gray-900">
              <span>{{ q.question }}</span>
              <svg class="h-4 w-4 shrink-0 text-gray-300 transition-transform" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </summary>
            <p v-if="q.reference_answer" class="whitespace-pre-wrap border-t border-gray-100 px-4 py-3 text-sm leading-relaxed text-gray-600">
              {{ q.reference_answer }}
            </p>
          </details>
        </div>
      </section>

      <!-- 学习记录：从学习计划进入时联动任务，否则独立记录 -->
      <div class="mt-8 rounded-2xl border border-gray-100 bg-white p-5">
        <p class="text-sm font-semibold text-gray-900">学习记录</p>
        <p v-if="learningStatus === 'completed'" class="mt-2 text-sm text-green-600">已完成学习 ✓</p>
        <p v-else-if="learningStatus === 'started'" class="mt-2 text-sm text-gray-500">学习中…完成后点击下方按钮</p>

        <div class="mt-3">
          <PrimaryButton v-if="learningStatus === 'idle'" :disabled="learningBusy" @click="start">
            {{ learningBusy ? '记录中…' : '开始学习' }}
          </PrimaryButton>
          <PrimaryButton v-else-if="learningStatus === 'started'" :disabled="learningBusy" @click="complete">
            {{ learningBusy ? '记录中…' : '完成学习' }}
          </PrimaryButton>
          <div v-else class="flex flex-col gap-2">
            <PrimaryButton v-if="completedPlanId" @click="router.push(`/learning/plan/${completedPlanId}`)">返回学习计划</PrimaryButton>
            <PrimaryButton v-else-if="taskId" @click="router.push('/learning/plan')">返回学习计划</PrimaryButton>
          </div>
        </div>
        <p v-if="learningError" class="mt-2 text-xs text-red-600">{{ learningError }}</p>
      </div>

      <div class="mt-4">
        <PrimaryButton @click="router.push('/learning/qa')">用 AI 问问这个知识</PrimaryButton>
      </div>
    </article>
  </div>
</template>

<style scoped>
details[open] summary svg {
  transform: rotate(180deg);
}
</style>
