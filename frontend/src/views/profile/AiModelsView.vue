<script setup>
import { onMounted, ref } from 'vue'

import PageHeader from '@/components/layout/PageHeader.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModelCard from '@/components/models/ModelCard.vue'
import ModelForm from '@/components/models/ModelForm.vue'
import ModelPickerSheet from '@/components/models/ModelPickerSheet.vue'
import { listModels, deleteModel, testModel } from '@/api/models'
import {
  ERROR_MESSAGES,
  FUNCTION_DEFINITIONS,
  getBindings,
  providerLabel,
  removeBindingsForModel,
  setBinding,
} from '@/utils/models'

const models = ref([])
const loading = ref(true)
const loadError = ref(false)

const showForm = ref(false)
const editingModel = ref(null)

const showPicker = ref(false)
const pickerFunction = ref(null)

const deleteTarget = ref(null)
const deleting = ref(false)

// modelId -> { status: idle | testing | success | error, message?, latency_ms? }
const testStates = ref({})

const bindings = ref(getBindings())

async function load() {
  loading.value = true
  loadError.value = false
  try {
    models.value = await listModels()
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editingModel.value = null
  showForm.value = true
}

function openEdit(model) {
  editingModel.value = model
  showForm.value = true
}

function onSaved() {
  showForm.value = false
  editingModel.value = null
  load()
}

function askDelete(model) {
  deleteTarget.value = model
}

async function confirmDelete() {
  const target = deleteTarget.value
  if (!target || deleting.value) return
  deleting.value = true
  try {
    await deleteModel(target.id)
    removeBindingsForModel(target.id)
    bindings.value = getBindings()
    deleteTarget.value = null
    load()
  } catch {
    // 删除失败：保留弹窗并允许重试；简单提示由控制台之外不暴露
  } finally {
    deleting.value = false
  }
}

async function runTest(model) {
  testStates.value[model.id] = { status: 'testing' }
  try {
    const result = await testModel(model.id)
    if (result.success) {
      testStates.value[model.id] = { status: 'success', latency_ms: result.latency_ms }
    } else {
      testStates.value[model.id] = {
        status: 'error',
        message: result.message || ERROR_MESSAGES[result.error_code] || '连接失败，请稍后重试。',
      }
    }
  } catch {
    testStates.value[model.id] = { status: 'error', message: '连接测试请求失败，请稍后重试。' }
  }
}

function openPicker(fn) {
  pickerFunction.value = fn
  showPicker.value = true
}

function onSelectModel(modelId) {
  setBinding(pickerFunction.value.id, modelId)
  bindings.value = getBindings()
  showPicker.value = false
}

function onClearBinding() {
  setBinding(pickerFunction.value.id, null)
  bindings.value = getBindings()
  showPicker.value = false
}

function onPickerAdd() {
  showPicker.value = false
  openAdd()
}

function boundModel(fn) {
  const id = bindings.value[fn.id]
  if (id == null) return null
  return models.value.find((m) => m.id === id) || null
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="AI 模型 / API" />

    <div class="px-5 py-4">
      <p class="text-xs text-gray-400">使用你自己的 API Key 连接 AI 模型，模型调用费用由对应服务商收取。</p>

      <!-- 我的模型 -->
      <section class="mt-6">
        <SectionTitle title="我的模型">
          <template #right>
            <button type="button" class="text-sm font-medium text-brand-600" @click="openAdd">添加模型</button>
          </template>
        </SectionTitle>

        <div class="mt-3">
          <p v-if="loading" class="py-12 text-center text-sm text-gray-400">加载中…</p>

          <div v-else-if="loadError" class="py-12 text-center">
            <p class="text-sm text-gray-500">暂时无法加载模型，请稍后重试</p>
            <button type="button" class="mt-3 text-sm font-medium text-brand-600" @click="load">重试</button>
          </div>

          <EmptyState
            v-else-if="!models.length"
            title="还没有配置 AI 模型"
            description="使用 AI 功能前，请先配置自己的模型 API。"
          >
            <template #action>
              <PrimaryButton @click="openAdd">添加第一个模型</PrimaryButton>
            </template>
          </EmptyState>

          <div v-else class="space-y-2">
            <ModelCard
              v-for="m in models"
              :key="m.id"
              :model="m"
              :test-state="testStates[m.id]"
              @test="runTest(m)"
              @edit="openEdit(m)"
              @delete="askDelete(m)"
            />
          </div>
        </div>
      </section>

      <!-- 功能模型 -->
      <section class="mt-8">
        <SectionTitle title="功能模型配置" />
        <p class="mt-1 text-xs text-gray-400">选择不同功能使用的 AI 模型。</p>
        <div class="card mt-3 divide-y divide-gray-50">
          <button
            v-for="fn in FUNCTION_DEFINITIONS"
            :key="fn.id"
            type="button"
            class="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left"
            @click="openPicker(fn)"
          >
            <div class="min-w-0">
              <p class="text-sm font-medium text-gray-900">{{ fn.label }}</p>
              <p class="mt-0.5 text-xs text-gray-400">{{ fn.description }}</p>
            </div>
            <div class="flex shrink-0 items-center gap-1">
              <span v-if="boundModel(fn)" class="truncate text-sm text-brand-600">
                {{ providerLabel(boundModel(fn).provider) }} · {{ boundModel(fn).model }}
              </span>
              <span v-else class="text-xs text-gray-400">未配置</span>
              <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </div>
          </button>
        </div>
      </section>
    </div>

    <!-- 添加 / 编辑模型 -->
    <ModelForm v-if="showForm" :model="editingModel" @saved="onSaved" @cancel="showForm = false" />

    <!-- 功能模型选择器 -->
    <ModelPickerSheet
      v-if="showPicker && pickerFunction"
      :fn="pickerFunction"
      :models="models"
      :current-model-id="bindings[pickerFunction.id] ?? null"
      @select="onSelectModel"
      @clear="onClearBinding"
      @add="onPickerAdd"
      @close="showPicker = false"
    />

    <!-- 删除确认 -->
    <div v-if="deleteTarget" class="fixed inset-0 z-40 flex items-center justify-center px-6">
      <div class="absolute inset-0 bg-black/40" @click="deleteTarget = null"></div>
      <div class="relative w-full max-w-sm rounded-2xl bg-white p-5">
        <p class="text-base font-semibold text-gray-900">删除「{{ providerLabel(deleteTarget.provider) }}」？</p>
        <p class="mt-2 text-sm text-gray-500">删除后，使用该模型的功能配置将失效。</p>
        <div class="mt-5 flex gap-3">
          <button
            type="button"
            class="flex-1 rounded-2xl border border-gray-200 py-3 text-sm text-gray-600 active:bg-gray-50"
            @click="deleteTarget = null"
          >
            取消
          </button>
          <button
            type="button"
            class="flex-1 rounded-2xl bg-red-500 py-3 text-sm font-medium text-white disabled:bg-red-300"
            :disabled="deleting"
            @click="confirmDelete"
          >
            {{ deleting ? '删除中…' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
