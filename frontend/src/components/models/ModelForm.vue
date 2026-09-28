<script setup>
import { computed, ref } from 'vue'

import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import { createModel, updateModel } from '@/api/models'
import { MODEL_TYPE_OPTIONS, PROVIDER_OPTIONS, providerLabel } from '@/utils/models'

const props = defineProps({
  model: { type: Object, default: null },
})
const emit = defineEmits(['saved', 'cancel'])

const isEdit = computed(() => !!props.model)

const initialProvider = props.model?.provider || 'deepseek'
const initialPreset = PROVIDER_OPTIONS.find((p) => p.value === initialProvider)
const initialModelType = props.model?.capabilities?.embedding === 'supported' ? 'embedding' : 'text_generation'

const provider = ref(initialProvider)
const baseUrl = ref(props.model?.base_url || initialPreset?.baseUrl || '')
const modelName = ref(props.model?.model || initialPreset?.model || '')
const modelType = ref(initialModelType)
const apiKey = ref('') // 编辑时绝不复用旧 Key，留空表示保持不变
const showKey = ref(false)
const saving = ref(false)
const error = ref('')

const title = computed(() => (isEdit.value ? '编辑模型' : '添加模型'))

// 模型用途仅对 custom / OpenAI 兼容 provider 生效
const showModelType = computed(() => provider.value === 'custom')

function onProviderChange(value) {
  provider.value = value
  const preset = PROVIDER_OPTIONS.find((p) => p.value === value)
  baseUrl.value = preset?.baseUrl || ''
  modelName.value = preset?.model || ''
}

const canSave = computed(() => modelName.value.trim() !== '' && (isEdit.value || apiKey.value.trim() !== ''))

// Model 占位提示跟随 Provider 预设（如 DeepSeek → deepseek-flash），不硬编码模型名
const modelPlaceholder = computed(() => {
  const preset = PROVIDER_OPTIONS.find((p) => p.value === provider.value)
  return preset?.model || 'model 名称'
})

function extractMessage(e) {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) return detail[0]?.msg || '请求失败，请稍后重试。'
  return '保存失败，请稍后重试。'
}

async function save() {
  if (!canSave.value || saving.value) return
  saving.value = true
  error.value = ''
  const payload = {
    name: providerLabel(provider.value),
    provider: provider.value,
    model: modelName.value.trim(),
    base_url: baseUrl.value.trim() || null,
    model_type: modelType.value,
  }
  if (apiKey.value.trim()) payload.api_key = apiKey.value.trim()
  try {
    if (isEdit.value) {
      await updateModel(props.model.id, payload)
    } else {
      await createModel(payload)
    }
    emit('saved')
  } catch (e) {
    error.value = extractMessage(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-30 flex flex-col bg-white">
    <header class="flex h-14 shrink-0 items-center gap-1 border-b border-gray-100 px-3">
      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-full text-gray-600 hover:bg-gray-100"
        aria-label="返回"
        @click="$emit('cancel')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
      </button>
      <h1 class="text-base font-semibold text-gray-900">{{ title }}</h1>
    </header>

    <div class="flex-1 overflow-y-auto px-5 py-5">
      <!-- Provider -->
      <div>
        <label class="text-sm font-medium text-gray-900">Provider</label>
        <div class="mt-2 flex flex-wrap gap-2">
          <button
            v-for="p in PROVIDER_OPTIONS"
            :key="p.value"
            type="button"
            class="rounded-full border px-4 py-2 text-sm transition-colors"
            :class="provider === p.value ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
            @click="onProviderChange(p.value)"
          >
            {{ p.label }}
          </button>
        </div>
      </div>

      <!-- 模型用途（仅 custom / OpenAI 兼容 provider 生效） -->
      <div v-if="showModelType" class="mt-5">
        <label class="text-sm font-medium text-gray-900">模型用途</label>
        <div class="mt-2 flex flex-wrap gap-2">
          <button
            v-for="t in MODEL_TYPE_OPTIONS"
            :key="t.value"
            type="button"
            class="rounded-full border px-4 py-2 text-sm transition-colors"
            :class="modelType === t.value ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
            @click="modelType = t.value"
          >
            {{ t.label }}
          </button>
        </div>
        <p class="mt-1 text-xs text-gray-400">自定义模型需声明用途（Embedding 用于知识库检索）。</p>
      </div>

      <!-- Base URL -->
      <div class="mt-5">
        <label class="text-sm font-medium text-gray-900">API Base URL</label>
        <input
          v-model="baseUrl"
          type="text"
          placeholder="https://api.deepseek.com"
          class="mt-2 w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm text-gray-900 focus:border-brand-500 focus:outline-none"
        />
        <p class="mt-1 text-xs text-gray-400">部分 Provider 已自动填充，可手动修改。</p>
      </div>

      <!-- API Key -->
      <div class="mt-5">
        <label class="text-sm font-medium text-gray-900">API Key</label>
        <div class="relative mt-2">
          <input
            v-model="apiKey"
            :type="showKey ? 'text' : 'password'"
            :placeholder="isEdit ? '保持当前 API Key（留空则不修改）' : 'sk-...'"
            autocomplete="off"
            class="w-full rounded-2xl border border-gray-200 px-4 py-3 pr-16 text-sm text-gray-900 focus:border-brand-500 focus:outline-none"
          />
          <button
            type="button"
            class="absolute inset-y-0 right-0 flex items-center px-4 text-xs text-gray-400 hover:text-gray-600"
            @click="showKey = !showKey"
          >
            {{ showKey ? '隐藏' : '显示' }}
          </button>
        </div>
        <p class="mt-1 text-xs text-gray-400">Key 仅保存在服务端，前端不回显完整内容。</p>
      </div>

      <!-- Model -->
      <div class="mt-5">
        <label class="text-sm font-medium text-gray-900">Model</label>
        <input
          v-model="modelName"
          type="text"
          :placeholder="modelPlaceholder"
          class="mt-2 w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm text-gray-900 focus:border-brand-500 focus:outline-none"
        />
      </div>

      <p v-if="error" class="mt-4 text-sm text-red-500">{{ error }}</p>
    </div>

    <div class="shrink-0 border-t border-gray-100 p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">
      <PrimaryButton :disabled="saving || !canSave" @click="save">
        {{ saving ? '保存中…' : '保存' }}
      </PrimaryButton>
    </div>
  </div>
</template>
