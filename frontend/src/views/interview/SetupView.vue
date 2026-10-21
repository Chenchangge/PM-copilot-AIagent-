<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import ChoiceGroup from '@/components/ui/ChoiceGroup.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { createInterviewSession } from '@/api/interview'
import { resolveModel } from '@/api/models'
import { difficultyLevels, interviewTypes, productDirections } from '@/constants/interview'
import { extractInterviewError, needsModelConfig } from '@/utils/interview'

const route = useRoute()
const router = useRouter()

const direction = ref(productDirections.includes(route.query.direction) ? route.query.direction : productDirections[0])
const difficulty = ref('中等')
const type = ref(interviewTypes.includes(route.query.type) ? route.query.type : interviewTypes[0])
const starting = ref(false)
const error = ref('')
const errorCode = ref('')

async function start() {
  if (starting.value) return
  starting.value = true
  error.value = ''
  errorCode.value = ''
  try {
    // 进入会话前先预检：缺模型时在设置页给出出口，避免写完回答才报错。
    const resolved = await resolveModel(['text_generation', 'reasoning', 'structured_output'])
    if (!resolved.models?.length && !resolved.using_server_default) {
      errorCode.value = 'INTERVIEW_MODEL_NOT_FOUND'
      error.value = '还没有可用于模拟面试的文本生成模型，请先配置模型，或先去知识库看看。'
      return
    }
    const data = await createInterviewSession({
      direction: direction.value,
      difficulty: difficulty.value,
      interview_type: type.value,
    })
    router.push({ name: 'interview-session', params: { id: data.session_id } })
  } catch (e) {
    const { code, message } = extractInterviewError(e)
    errorCode.value = code
    error.value = message
  } finally {
    starting.value = false
  }
}
</script>

<template>
  <div class="flex h-[calc(100dvh-3.5rem-env(safe-area-inset-bottom))] flex-col">
    <PageHeader title="模拟面试" :back="false" />
    <div class="flex-1 space-y-8 overflow-y-auto px-5 py-6">
      <section>
        <SectionTitle title="产品方向" />
        <ChoiceGroup v-model="direction" :options="productDirections" class="mt-3" />
      </section>
      <section>
        <SectionTitle title="难度" />
        <ChoiceGroup v-model="difficulty" :options="difficultyLevels" class="mt-3" />
      </section>
      <section>
        <SectionTitle title="面试类型" />
        <ChoiceGroup v-model="type" :options="interviewTypes" class="mt-3" />
      </section>

      <div v-if="error" class="rounded-2xl bg-red-50 p-4">
        <p class="text-sm text-red-600">{{ error }}</p>
        <div v-if="needsModelConfig(errorCode)" class="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-full bg-brand-600 px-3.5 py-2 text-xs font-medium text-white"
            @click="router.push('/profile/ai-models')"
          >
            去配置模型
          </button>
          <button
            type="button"
            class="rounded-full border border-gray-200 bg-white px-3.5 py-2 text-xs text-gray-600"
            @click="router.push('/learning/knowledge')"
          >
            先看看知识库
          </button>
        </div>
      </div>
    </div>
    <div class="shrink-0 border-t border-gray-100 bg-white px-5 py-3">
      <p class="mb-2 text-center text-[11px] text-gray-400">开始前会检查文本生成模型；缺模型会在这里提示</p>
      <PrimaryButton :disabled="starting" @click="start">{{ starting ? '检查中…' : '开始面试' }}</PrimaryButton>
    </div>
  </div>
</template>
