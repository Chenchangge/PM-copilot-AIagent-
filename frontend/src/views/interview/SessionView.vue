<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import { mockQuestions, mockSession } from '@/mock'

const route = useRoute()
const router = useRouter()

const current = ref(0)
const phase = ref('question') // 'question' | 'followup'
const answer = ref('')

const q = computed(() => mockQuestions[current.value])
const isLast = computed(() => current.value === mockQuestions.length - 1)
const progress = computed(() => ((current.value + (phase.value === 'followup' ? 1 : 0)) / mockQuestions.length) * 100)
const buttonLabel = computed(() =>
  phase.value === 'question' ? '提交回答' : isLast.value ? '结束面试，查看报告' : '下一题'
)

function submit() {
  if (!answer.value.trim()) return
  if (phase.value === 'question') {
    phase.value = 'followup'
    answer.value = ''
  } else if (isLast.value) {
    router.push({ name: 'interview-report', params: { id: route.params.id } })
  } else {
    current.value += 1
    phase.value = 'question'
    answer.value = ''
  }
}
</script>

<template>
  <div>
    <PageHeader title="AI 面试" />
    <div class="px-5 py-5">
      <div class="flex items-center justify-between text-xs text-gray-500">
        <span>{{ mockSession.direction }} · {{ mockSession.difficulty }}</span>
        <span>第 {{ current + 1 }} / {{ mockQuestions.length }} 题</span>
      </div>
      <ProgressBar :value="progress" size="sm" class="mt-2" />

      <div class="card mt-6 p-5">
        <p class="text-xs font-medium text-brand-600">面试官</p>
        <p class="mt-2 text-base font-medium leading-relaxed text-gray-900">{{ q.text }}</p>
      </div>

      <div v-if="phase === 'followup'" class="mt-3 rounded-2xl bg-brand-50 p-4">
        <p class="text-xs font-medium text-brand-700">追问</p>
        <p class="mt-1 text-sm text-gray-700">{{ q.followUp }}</p>
      </div>

      <div class="mt-5">
        <textarea
          v-model="answer"
          rows="5"
          :placeholder="phase === 'question' ? '输入你的回答…' : '回答追问…'"
          class="w-full resize-none rounded-2xl border border-gray-200 bg-white p-4 text-sm leading-relaxed focus:border-brand-500 focus:outline-none"
        ></textarea>
      </div>

      <div class="mt-4">
        <PrimaryButton @click="submit">{{ buttonLabel }}</PrimaryButton>
      </div>

      <p class="mt-4 text-center text-xs text-gray-400">AI 面试将在后续阶段接入，当前为 Mock 交互。</p>
    </div>
  </div>
</template>
