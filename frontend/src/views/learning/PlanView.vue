<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import LearningTabs from '@/components/learning/LearningTabs.vue'
import ChoiceGroup from '@/components/ui/ChoiceGroup.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { createPlan, estimatePlan, getPlanTaxonomy, listPlans } from '@/api/learning'
import { extractInterviewError } from '@/utils/interview'

const router = useRouter()

const loading = ref(true)
const error = ref('')
const taxonomy = ref(null)
const currentPlan = ref(null)

// 目标选择：path = 三张路径卡；custom = 折叠区里的分类/专题/方向
const mode = ref('path')
const selectedPathId = ref('')

// 自定义目标
const customOpen = ref(false)
const customType = ref('category') // category | topic | direction（不再提供 tag）
const customCategoryId = ref('')
const customTarget = ref(null)
const topicSearch = ref('')
const showAllCategories = ref(false)

// 高级设置：当前水平 / 学习强度 / 目标面试方向
const advancedOpen = ref(false)
const level = ref('基础')
const dailyMinutes = ref('30')
const intensity = ref('标准')
const directionId = ref('')
const planMode = ref('full') // full | crash

// 估算 / 创建
const estimating = ref(false)
const estimate = ref(null)
const selectedDays = ref('')
const creating = ref(false)

let taxRequestSeq = 0

const customTypes = [
  { id: 'category', label: '按分类' },
  { id: 'topic', label: '按专题' },
  { id: 'direction', label: '按方向' },
]

const paths = computed(() => taxonomy.value?.paths || [])
const categories = computed(() => taxonomy.value?.categories || [])
const featuredCategories = computed(() => categories.value.filter((c) => c.featured))
const otherCategories = computed(() => categories.value.filter((c) => !c.featured))
const visibleCategories = computed(() =>
  showAllCategories.value ? [...featuredCategories.value, ...otherCategories.value] : featuredCategories.value,
)
const topicGroups = computed(() => taxonomy.value?.topics || {})
const customCategoryTopics = computed(() => topicGroups.value[customCategoryId.value] || [])
const filteredTopics = computed(() => {
  const q = topicSearch.value.trim().toLowerCase()
  const rows = q
    ? customCategoryTopics.value.filter((t) => t.name.toLowerCase().includes(q) || t.id.toLowerCase().includes(q))
    : customCategoryTopics.value
  return rows.slice(0, 8)
})
const selectedPath = computed(() => paths.value.find((p) => p.id === selectedPathId.value) || null)
const levelOptions = computed(() => taxonomy.value?.levels || ['入门', '基础', '进阶'])
const intensityOptions = computed(() => taxonomy.value?.intensities || ['轻量', '标准', '高强度'])
const dailyMinuteOptions = computed(() => (taxonomy.value?.daily_minutes || [15, 30, 45, 60]).map(String))
const dayChoices = computed(() => (estimate.value?.day_choices || []).map(String))
const difficultyChips = computed(() =>
  Object.entries(estimate.value?.difficulty_counts || {}).map(([label, count]) => ({ label, count })),
)

const customTargetCount = computed(() => {
  const target = customTarget.value
  if (!target) return 0
  if (target.type === 'category') {
    return categories.value.find((c) => c.id === target.id)?.knowledge_count || 0
  }
  if (target.type === 'topic') {
    const rows = topicGroups.value[customCategoryId.value] || []
    return rows.find((t) => t.id === target.id)?.knowledge_count || 0
  }
  return 1
})

const canEstimate = computed(() => {
  if (mode.value === 'path') return !!selectedPath.value && selectedPath.value.knowledge_count > 0
  return !!customTarget.value && customTargetCount.value > 0
})

function isPathSelected(path) {
  return mode.value === 'path' && selectedPathId.value === path.id
}

function isCategorySelected(cat) {
  return mode.value === 'custom' && customTarget.value?.type === 'category' && customTarget.value.id === cat.id
}

function isTopicSelected(topic) {
  return mode.value === 'custom' && customTarget.value?.type === 'topic' && customTarget.value.id === topic.id
}

function isDirectionSelected(direction) {
  return mode.value === 'custom' && customTarget.value?.type === 'direction' && customTarget.value.id === direction
}

function clearEstimate() {
  estimate.value = null
  selectedDays.value = ''
  error.value = ''
}

function selectPath(path) {
  if (!path || path.knowledge_count === 0) return
  mode.value = 'path'
  selectedPathId.value = path.id
  clearEstimate()
}

function selectCustom(type, id, name) {
  mode.value = 'custom'
  customTarget.value = { type, id, name }
  clearEstimate()
}

function chooseCategory(cat) {
  if (cat.knowledge_count === 0) return
  customCategoryId.value = cat.id
  if (customType.value === 'category') {
    selectCustom('category', cat.id, cat.name)
  }
}

function chooseTopicCategory(cat) {
  if (cat.knowledge_count === 0) return
  customCategoryId.value = cat.id
  topicSearch.value = ''
  if (customTarget.value?.type === 'topic') customTarget.value = null
  clearEstimate()
}

function chooseTopic(topic) {
  if (topic.knowledge_count === 0) return
  selectCustom('topic', topic.id, topic.name)
}

function chooseDirection(direction) {
  selectCustom('direction', direction, direction)
}

function switchCustomType(type) {
  if (customType.value === type) return
  customType.value = type
  customTarget.value = null
  topicSearch.value = ''
  clearEstimate()
}

function applyTaxonomy(tax) {
  taxonomy.value = tax
  if (!tax.paths?.length) {
    selectedPathId.value = ''
    return
  }
  const current = tax.paths.find((p) => p.id === selectedPathId.value)
  if (!current || current.knowledge_count === 0) {
    const first = tax.paths.find((p) => p.knowledge_count > 0)
    selectedPathId.value = first?.id || ''
    if (!first) mode.value = 'custom'
  }
}

async function fetchTaxonomy() {
  return getPlanTaxonomy({
    current_level: level.value,
    daily_minutes: Number(dailyMinutes.value),
    intensity: intensity.value,
  })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [taxResult, plansResult] = await Promise.allSettled([fetchTaxonomy(), listPlans()])
    if (taxResult.status === 'rejected') throw taxResult.reason
    applyTaxonomy(taxResult.value)
    if (plansResult.status === 'fulfilled') {
      currentPlan.value =
        (plansResult.value.items || []).find((p) => p.status === 'active' || p.status === 'paused') || null
    }
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    loading.value = false
  }
}

async function refreshTaxonomy() {
  if (!taxonomy.value) return
  const seq = ++taxRequestSeq
  clearEstimate()
  try {
    const tax = await fetchTaxonomy()
    if (seq !== taxRequestSeq) return
    applyTaxonomy(tax)
  } catch {
    // 保留旧选项，估算时仍会给出具体错误，不因刷新失败白屏
  }
}

function buildPayload() {
  const base = {
    current_level: level.value,
    daily_minutes: Number(dailyMinutes.value),
    intensity: intensity.value,
    mode: planMode.value,
  }
  if (mode.value === 'path') {
    return { path_id: selectedPathId.value, ...base }
  }
  return {
    target_type: customTarget.value.type,
    target_id: customTarget.value.id,
    direction_id: directionId.value || null,
    ...base,
  }
}

async function runEstimate() {
  if (!canEstimate.value || estimating.value) return
  estimating.value = true
  clearEstimate()
  try {
    const data = await estimatePlan(buildPayload())
    estimate.value = data
    selectedDays.value = String(data.recommended_days)
    // 估算后收起配置区，把结果放到首屏可见范围；用户仍可重新展开修改。
    customOpen.value = false
    advancedOpen.value = false
    showAllCategories.value = false
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    estimating.value = false
  }
}

async function runCreate() {
  if (!estimate.value || creating.value || !selectedDays.value) return
  creating.value = true
  error.value = ''
  try {
    const data = await createPlan({
      ...buildPayload(),
      selected_days: Number(selectedDays.value),
    })
    router.push(`/learning/plan/${data.id}`)
  } catch (e) {
    error.value = extractInterviewError(e).message
  } finally {
    creating.value = false
  }
}

watch([level, dailyMinutes, intensity], refreshTaxonomy)
watch(planMode, clearEstimate)

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

    <div v-else class="px-5 pt-4">
      <header>
        <h1 class="text-xl font-bold tracking-tight text-gray-900">学习计划</h1>
        <p class="mt-1 text-xs text-gray-500">选择你的目标，系统排好每天的任务</p>
      </header>

      <!-- 当前计划：压成一条，避免把首屏路径卡推出屏幕 -->
      <RouterLink
        v-if="currentPlan"
        :to="`/learning/plan/${currentPlan.id}`"
        class="mt-3 flex items-center justify-between rounded-xl border border-gray-100 bg-white px-3 py-2.5"
      >
        <span class="min-w-0 truncate text-xs text-gray-600">进行中：{{ currentPlan.title }}</span>
        <span class="ml-2 shrink-0 text-xs font-medium text-brand-600">{{ currentPlan.progress_percent }}%</span>
      </RouterLink>

      <!-- 学习路径卡（默认首屏只露这 3 张 + 时间 + 估算） -->
      <section class="mt-5">
        <div class="space-y-2.5">
          <button
            v-for="path in paths"
            :key="path.id"
            type="button"
            class="w-full rounded-2xl border p-4 text-left transition-colors"
            :class="[
              isPathSelected(path)
                ? 'border-brand-600 bg-brand-50/40 ring-1 ring-brand-600'
                : 'border-gray-100 bg-white active:bg-gray-50',
              path.knowledge_count === 0 ? 'opacity-60' : '',
            ]"
            :disabled="path.knowledge_count === 0"
            @click="selectPath(path)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-sm font-semibold text-gray-900">{{ path.name }}</p>
                <p class="mt-0.5 text-xs text-gray-500">{{ path.subtitle }}</p>
              </div>
              <span class="shrink-0 rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-semibold text-brand-700">
                {{ path.days ? `${path.days} 天` : '暂无' }}
              </span>
            </div>
            <div class="mt-2.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-gray-500">
              <span>{{ path.knowledge_count }} 个知识点</span>
              <span v-if="path.question_count">· {{ path.question_count }} 道高频题</span>
              <span v-if="path.days && path.days !== path.target_days" class="text-gray-400">
                · 冲刺目标 {{ path.target_days }} 天
              </span>
              <span v-if="path.knowledge_count === 0" class="text-amber-600">当前水平暂无内容</span>
            </div>
          </button>
        </div>
      </section>

      <!-- 每日学习时间 -->
      <section class="mt-5">
        <div class="flex items-baseline justify-between">
          <h2 class="text-sm font-semibold text-gray-900">每日学习时间</h2>
          <span class="text-[11px] text-gray-400">分钟</span>
        </div>
        <ChoiceGroup v-model="dailyMinutes" :options="dailyMinuteOptions" class="mt-2.5" />
      </section>

      <section class="mt-4">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-900">估算模式</h2>
          <span class="text-[11px] text-gray-400">核心速成 ≤14 天</span>
        </div>
        <div class="mt-2 grid grid-cols-2 gap-2">
          <button
            type="button"
            class="rounded-xl border px-3 py-2.5 text-xs transition-colors"
            :class="planMode === 'full' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white text-gray-600'"
            @click="planMode = 'full'"
          >
            完整路径
          </button>
          <button
            type="button"
            class="rounded-xl border px-3 py-2.5 text-xs transition-colors"
            :class="planMode === 'crash' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white text-gray-600'"
            @click="planMode = 'crash'"
          >
            核心速成
          </button>
        </div>
      </section>

      <div class="mt-4">
        <PrimaryButton :disabled="estimating || !canEstimate" @click="runEstimate">
          {{ estimating ? '分析中…' : '开始估算' }}
        </PrimaryButton>
      </div>

      <!-- 两个折叠入口：默认首屏可点击配置项控制在 10 个以内 -->
      <div class="mt-3 flex items-center justify-between text-xs">
        <button type="button" class="text-gray-500" @click="advancedOpen = !advancedOpen">
          更多设置 · {{ level }} / {{ intensity }}
          <span class="text-gray-300">{{ advancedOpen ? '▴' : '▾' }}</span>
        </button>
        <button type="button" class="text-gray-500" @click="customOpen = !customOpen">
          自定义目标
          <span class="text-gray-300">{{ customOpen ? '▴' : '▾' }}</span>
        </button>
      </div>

      <!-- 更多设置：当前水平 / 学习强度真正参与计算 -->
      <section v-if="advancedOpen" class="card mt-3 p-4">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-900">当前水平</h2>
          <span class="text-[11px] text-gray-400">影响知识点数量</span>
        </div>
        <ChoiceGroup v-model="level" :options="levelOptions" class="mt-2.5" />

        <div class="mt-4 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-gray-900">学习强度</h2>
          <span class="text-[11px] text-gray-400">影响每日任务量</span>
        </div>
        <ChoiceGroup v-model="intensity" :options="intensityOptions" class="mt-2.5" />

        <div class="mt-4">
          <label class="text-sm font-semibold text-gray-900" for="plan-direction">目标面试方向（可选）</label>
          <select
            id="plan-direction"
            v-model="directionId"
            class="mt-2 w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-700"
          >
            <option value="">暂不选择</option>
            <option v-for="d in taxonomy.directions" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>

        <p class="mt-3 text-[11px] leading-relaxed text-gray-400">
          入门只看入门/基础，基础增加到进阶，进阶放开全部难度；轻量按每日时长的 70% 排课，高强度按 130%。
        </p>
      </section>

      <!-- 自定义目标：分类只露 5 个，专题二级联动，彻底移除标签 -->
      <section v-if="customOpen" class="card mt-3 p-4">
        <p class="mb-2 text-[11px] text-gray-400">目标类型</p>
        <div class="flex rounded-full bg-gray-100 p-1">
          <button
            v-for="t in customTypes"
            :key="t.id"
            type="button"
            class="flex-1 rounded-full py-1.5 text-xs transition-colors"
            :class="customType === t.id ? 'bg-white font-medium text-gray-900 shadow-sm' : 'text-gray-500'"
            @click="switchCustomType(t.id)"
          >
            {{ t.label }}
          </button>
        </div>

        <!-- 按分类 -->
        <div v-if="customType === 'category'" class="mt-3">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="cat in visibleCategories"
              :key="cat.id"
              type="button"
              class="rounded-full border px-3 py-2 text-xs transition-colors"
              :class="
                isCategorySelected(cat)
                  ? 'border-brand-600 bg-brand-600 text-white'
                  : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'
              "
              :disabled="cat.knowledge_count === 0"
              @click="chooseCategory(cat)"
            >
              {{ cat.name }}
              <span class="ml-0.5 opacity-70">{{ cat.knowledge_count }}</span>
            </button>
          </div>
          <button
            v-if="otherCategories.length"
            type="button"
            class="mt-2 text-xs font-medium text-brand-600"
            @click="showAllCategories = !showAllCategories"
          >
            {{ showAllCategories ? '收起分类' : `更多分类（${otherCategories.length}）` }}
          </button>
        </div>

        <!-- 按专题：先选分类，再选专题（二级联动） -->
        <div v-else-if="customType === 'topic'" class="mt-3">
          <p class="text-[11px] text-gray-400">先选择分类，再选择专题</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="cat in visibleCategories"
              :key="cat.id"
              type="button"
              class="rounded-full border px-3 py-2 text-xs transition-colors"
              :class="
                customCategoryId === cat.id
                  ? 'border-brand-600 bg-brand-50 text-brand-700'
                  : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'
              "
              :disabled="cat.knowledge_count === 0"
              @click="chooseTopicCategory(cat)"
            >
              {{ cat.name }}
            </button>
          </div>
          <button
            v-if="otherCategories.length"
            type="button"
            class="mt-2 text-xs font-medium text-brand-600"
            @click="showAllCategories = !showAllCategories"
          >
            {{ showAllCategories ? '收起分类' : `更多分类（${otherCategories.length}）` }}
          </button>

          <div v-if="customCategoryId" class="mt-3">
            <input
              v-if="customCategoryTopics.length > 8"
              v-model="topicSearch"
              type="search"
              placeholder="搜索专题"
              class="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700 placeholder:text-gray-400"
            />
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="topic in filteredTopics"
                :key="topic.id"
                type="button"
                class="rounded-full border px-3 py-2 text-xs transition-colors"
                :class="
                  isTopicSelected(topic)
                    ? 'border-brand-600 bg-brand-600 text-white'
                    : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'
                "
                :disabled="topic.knowledge_count === 0"
                @click="chooseTopic(topic)"
              >
                {{ topic.name }}
                <span class="ml-0.5 opacity-70">{{ topic.knowledge_count }}</span>
              </button>
            </div>
            <p v-if="!filteredTopics.length" class="mt-2 text-xs text-gray-400">该分类下暂无可选专题</p>
          </div>
        </div>

        <!-- 按方向 -->
        <div v-else class="mt-3">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="d in taxonomy.directions"
              :key="d"
              type="button"
              class="rounded-full border px-3 py-2 text-xs transition-colors"
              :class="
                isDirectionSelected(d)
                  ? 'border-brand-600 bg-brand-600 text-white'
                  : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'
              "
              @click="chooseDirection(d)"
            >
              {{ d }}
            </button>
          </div>
        </div>

        <p
          v-if="mode === 'custom' && customTarget"
          class="mt-3 rounded-xl bg-brand-50 px-3 py-2 text-xs text-brand-700"
        >
          已选：{{ customTarget.name }}
          <span v-if="customTarget.type === 'category'">（{{ customTargetCount }} 个知识点）</span>
          <span v-if="customTarget.type === 'topic'">（{{ customTargetCount }} 个知识点）</span>
        </p>
      </section>

      <div v-if="error && taxonomy" class="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-600">{{ error }}</div>

      <!-- 估算结果（压缩纵向占用，保证整页不超过 1.5 屏） -->
      <section v-if="estimate" class="card mt-3 p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-[11px] font-medium text-brand-600">估算结果</p>
            <h2 class="mt-0.5 truncate text-base font-semibold text-gray-900">{{ estimate.target.name }}</h2>
          </div>
          <div class="flex shrink-0 flex-col items-end gap-1">
            <span class="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-600">
              {{ estimate.recommended_days }} 天
            </span>
            <span class="text-[10px] text-brand-600">{{ estimate.mode === 'crash' ? '核心速成' : '完整路径' }}</span>
          </div>
        </div>

        <div class="mt-2.5 grid grid-cols-3 gap-2">
          <div class="rounded-xl bg-gray-50 p-2.5">
            <p class="text-[11px] text-gray-400">知识点</p>
            <p class="mt-0.5 text-base font-semibold text-gray-900">{{ estimate.knowledge_count }}</p>
          </div>
          <div class="rounded-xl bg-gray-50 p-2.5">
            <p class="text-[11px] text-gray-400">总时长</p>
            <p class="mt-0.5 text-base font-semibold text-gray-900">{{ estimate.total_minutes }}<span class="ml-0.5 text-[11px] font-normal text-gray-500">分钟</span></p>
          </div>
          <div class="rounded-xl bg-gray-50 p-2.5">
            <p class="text-[11px] text-gray-400">每日有效</p>
            <p class="mt-0.5 text-base font-semibold text-gray-900">{{ estimate.effective_daily_minutes }}<span class="ml-0.5 text-[11px] font-normal text-gray-500">分钟</span></p>
          </div>
        </div>

        <div class="mt-2 flex flex-wrap gap-1.5">
          <span
            v-for="d in difficultyChips"
            :key="d.label"
            class="rounded-full bg-gray-100 px-2 py-1 text-[11px] text-gray-600"
          >
            {{ d.label }} {{ d.count }}
          </span>
          <span class="rounded-full bg-gray-100 px-2 py-1 text-[11px] text-gray-600">
            每天约 {{ estimate.recommended_tasks_per_day }} 个任务
          </span>
        </div>

        <div v-if="estimate.key_topics.length" class="mt-2.5">
          <p class="text-[11px] text-gray-400">学习重点</p>
          <p class="mt-0.5 line-clamp-2 text-xs leading-relaxed text-gray-600">{{ estimate.key_topics.join('、') }}</p>
        </div>

        <p
          v-if="estimate.explanation"
          class="mt-2.5 line-clamp-2 rounded-xl bg-gray-50 p-2.5 text-xs leading-relaxed text-gray-600"
        >
          {{ estimate.explanation }}
        </p>

        <div class="mt-2.5">
          <div class="flex items-center justify-between">
            <p class="text-[11px] text-gray-400">调整天数</p>
            <p class="text-[11px] text-gray-400">推荐 {{ estimate.recommended_days }} 天</p>
          </div>
          <ChoiceGroup v-model="selectedDays" :options="dayChoices" class="mt-1.5" />
        </div>

        <div class="mt-3">
          <PrimaryButton :disabled="creating" @click="runCreate">
            {{ creating ? '创建中…' : `创建 ${selectedDays} 天计划` }}
          </PrimaryButton>
        </div>
      </section>
    </div>
  </div>
</template>
