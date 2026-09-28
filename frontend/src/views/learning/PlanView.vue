<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import LearningTabs from '@/components/learning/LearningTabs.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import ChoiceGroup from '@/components/ui/ChoiceGroup.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import { createPlan, estimatePlan, getLearningTaxonomy, listPlans } from '@/api/learning'
import { extractInterviewError } from '@/utils/interview'

const router = useRouter()

const loading = ref(true)
const error = ref('')
const taxonomy = ref(null)
const currentPlan = ref(null)

// 表单
const targetType = ref('category')
const targetId = ref('')
const level = ref('入门')
const dailyMinutes = ref('30')
const intensity = ref('标准')
const directionId = ref('')

// 估算结果
const estimating = ref(false)
const estimate = ref(null)
const selectedDays = ref(null)

const creating = ref(false)

const targetTypes = [
  { id: 'category', label: '分类' },
  { id: 'topic', label: '专题' },
  { id: 'tag', label: '标签' },
  { id: 'direction', label: '方向' },
]

const targetOptions = computed(() => {
  const t = taxonomy.value
  if (!t) return []
  if (targetType.value === 'tag') return t.tags || []
  if (targetType.value === 'topic') return (t.topics || []).map((tp) => tp.name)
  if (targetType.value === 'direction') return t.directions || []
  return (t.categories || []).map((c) => c.name)
})

// 方向作为目标时，direction_id 即目标本身；否则取可选的「目标面试方向」
const effectiveDirectionId = computed(() =>
  targetType.value === 'direction' ? targetId.value || null : directionId.value || null
)

function selectTarget(name) {
  const t = taxonomy.value
  if (!t) return
  if (targetType.value === 'tag' || targetType.value === 'direction') {
    targetId.value = name
    return
  }
  if (targetType.value === 'topic') {
    const tp = t.topics.find((x) => x.name === name)
    targetId.value = tp ? tp.id : name
    return
  }
  const cat = t.categories.find((c) => c.name === name)
  targetId.value = cat ? cat.id : name
}

function isSelected(name) {
  const t = taxonomy.value
  if (!t) return false
  if (targetType.value === 'tag' || targetType.value === 'direction') return targetId.value === name
  if (targetType.value === 'topic') {
    const tp = t.topics.find((x) => x.name === name)
    return targetId.value === (tp ? tp.id : name)
  }
  const cat = t.categories.find((c) => c.name === name)
  return targetId.value === (cat ? cat.id : name)
}

function switchType(type) {
  targetType.value = type
  targetId.value = ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [tax, plans] = await Promise.all([getLearningTaxonomy(), listPlans()])
    taxonomy.value = tax
    currentPlan.value = (plans.items || []).find((p) => p.status === 'active' || p.status === 'paused') || null
    if (tax.categories && tax.categories.length) {
      targetId.value = tax.categories[0].id
    }
  } catch {
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function runEstimate() {
  if (!targetId.value || estimating.value) return
  estimating.value = true
  error.value = ''
  try {
    const data = await estimatePlan({
      target_type: targetType.value,
      target_id: targetId.value,
      current_level: level.value,
      daily_minutes: Number(dailyMinutes.value),
      intensity: intensity.value,
      direction_id: effectiveDirectionId.value,
    })
    estimate.value = data
    selectedDays.value = data.recommended_days
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    estimating.value = false
  }
}

async function runCreate() {
  if (!estimate.value || creating.value) return
  creating.value = true
  error.value = ''
  try {
    const data = await createPlan({
      target_type: targetType.value,
      target_id: targetId.value,
      current_level: level.value,
      daily_minutes: Number(dailyMinutes.value),
      intensity: intensity.value,
      direction_id: effectiveDirectionId.value,
      selected_days: selectedDays.value,
    })
    router.push(`/learning/plan/${data.id}`)
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="pb-6">
    <LearningTabs />

    <div v-if="loading" class="px-5 py-16 text-center text-sm text-gray-400">加载中…</div>

    <div v-else-if="error && !taxonomy" class="px-5 py-16 text-center">
      <p class="text-sm text-gray-500">{{ error }}</p>
      <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="load">重新加载</button>
    </div>

    <div v-else class="px-5 pt-5">
      <!-- 当前计划 -->
      <RouterLink
        v-if="currentPlan"
        :to="`/learning/plan/${currentPlan.id}`"
        class="card block p-5 transition-colors hover:border-gray-200"
      >
        <div class="flex items-center justify-between">
          <p class="text-xs font-medium text-brand-600">当前学习计划</p>
          <span class="text-xs text-gray-400">{{ currentPlan.status === 'paused' ? '已暂停' : '进行中' }}</span>
        </div>
        <h2 class="mt-1 text-base font-semibold text-gray-900">{{ currentPlan.title }}</h2>
        <div class="mt-3 flex items-center gap-2">
          <ProgressBar :value="currentPlan.progress_percent" size="sm" class="flex-1" />
          <span class="text-xs text-gray-500">{{ currentPlan.progress_percent }}%</span>
        </div>
        <p class="mt-2 text-xs text-gray-400">
          已完成 {{ currentPlan.completed_knowledge_points }} / {{ currentPlan.total_knowledge_points }} 个知识点 · 第 {{ currentPlan.current_day_number }} / {{ currentPlan.selected_days }} 天
        </p>
      </RouterLink>

      <!-- 新计划表单 -->
      <section class="mt-6">
        <SectionTitle title="开始一个学习计划" />
        <p class="mt-1 text-xs text-gray-400">选择学习目标，系统会计算学习量并推荐学习周期</p>
      </section>

      <section class="mt-5">
        <div class="flex rounded-full bg-gray-100 p-1">
          <button
            v-for="t in targetTypes"
            :key="t.id"
            type="button"
            class="flex-1 rounded-full py-1.5 text-sm transition-colors"
            :class="targetType === t.id ? 'bg-white font-medium text-gray-900 shadow-sm' : 'text-gray-500'"
            @click="switchType(t.id)"
          >
            {{ t.label }}
          </button>
        </div>
      </section>

      <section class="mt-5">
        <SectionTitle :title="targetType === 'tag' ? '选择标签' : targetType === 'topic' ? '选择专题' : targetType === 'direction' ? '选择方向' : '选择分类'" />
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            v-for="name in targetOptions"
            :key="name"
            type="button"
            class="rounded-full border px-4 py-2 text-sm transition-colors"
            :class="isSelected(name) ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
            @click="selectTarget(name)"
          >
            {{ name }}
          </button>
        </div>
      </section>

      <section class="mt-5">
        <SectionTitle title="当前水平" />
        <ChoiceGroup v-model="level" :options="taxonomy.levels" class="mt-3" />
      </section>

      <section class="mt-5">
        <SectionTitle title="每日学习时间" />
        <ChoiceGroup v-model="dailyMinutes" :options="taxonomy.daily_minutes.map(String)" class="mt-3" />
      </section>

      <section class="mt-5">
        <SectionTitle title="学习强度" />
        <ChoiceGroup v-model="intensity" :options="taxonomy.intensities" class="mt-3" />
      </section>

      <section v-if="targetType !== 'direction'" class="mt-5">
        <SectionTitle title="目标面试方向（可选）" />
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-full border px-4 py-2 text-sm transition-colors"
            :class="!directionId ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
            @click="directionId = ''"
          >
            暂不选择
          </button>
          <button
            v-for="d in taxonomy.directions"
            :key="d"
            type="button"
            class="rounded-full border px-4 py-2 text-sm transition-colors"
            :class="directionId === d ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
            @click="directionId = d"
          >
            {{ d }}
          </button>
        </div>
      </section>

      <div class="mt-6">
        <PrimaryButton :disabled="estimating || !targetId" @click="runEstimate">
          {{ estimating ? '分析中…' : '估算学习周期' }}
        </PrimaryButton>
      </div>

      <!-- 估算结果 -->
      <section v-if="estimate" class="card mt-6 p-5">
        <div class="flex items-center justify-between">
          <p class="text-xs font-medium text-brand-600">学习目标</p>
          <p class="text-sm font-semibold text-gray-900">{{ estimate.target.name }}</p>
        </div>
        <div class="mt-4 grid grid-cols-2 gap-3">
          <div class="rounded-xl bg-gray-50 p-3">
            <p class="text-xs text-gray-400">知识点</p>
            <p class="mt-1 text-lg font-semibold text-gray-900">{{ estimate.knowledge_count }} 个</p>
          </div>
          <div class="rounded-xl bg-gray-50 p-3">
            <p class="text-xs text-gray-400">预计总时长</p>
            <p class="mt-1 text-lg font-semibold text-gray-900">{{ estimate.total_minutes }} 分钟</p>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-between rounded-xl bg-brand-50 p-3">
          <div>
            <p class="text-xs text-brand-600">推荐学习周期</p>
            <p class="mt-0.5 text-lg font-semibold text-brand-700">{{ estimate.recommended_days }} 天</p>
          </div>
          <p class="text-right text-xs text-brand-600">
            建议每日 {{ estimate.recommended_daily_minutes }} 分钟<br />预计 {{ estimate.recommended_days }} 天完成
          </p>
        </div>

        <div v-if="estimate.key_topics.length" class="mt-4">
          <p class="text-xs text-gray-400">学习重点</p>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <span v-for="k in estimate.key_topics" :key="k" class="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600">{{ k }}</span>
          </div>
        </div>

        <div v-if="estimate.prerequisites.length" class="mt-4">
          <p class="text-xs text-gray-400">前置知识</p>
          <p class="mt-1 text-xs text-gray-600">{{ estimate.prerequisites.map((p) => p.title).join('、') }}</p>
        </div>

        <p v-if="estimate.explanation" class="mt-4 rounded-xl bg-gray-50 p-3 text-xs leading-relaxed text-gray-600">{{ estimate.explanation }}</p>

        <div class="mt-4">
          <p class="text-xs text-gray-400">调整天数</p>
          <ChoiceGroup
            v-model="selectedDays"
            :options="estimate.day_choices.map(String)"
            class="mt-2"
          />
        </div>

        <div class="mt-5">
          <PrimaryButton :disabled="creating" @click="runCreate">
            {{ creating ? '创建中…' : `创建 ${selectedDays} 天计划` }}
          </PrimaryButton>
        </div>
      </section>

      <div v-if="error && taxonomy" class="mt-4 rounded-2xl bg-red-50 p-4 text-sm text-red-600">{{ error }}</div>
    </div>
  </div>
</template>
