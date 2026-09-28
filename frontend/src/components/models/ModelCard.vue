<script setup>
import { computed } from 'vue'

import CapabilityBadge from './CapabilityBadge.vue'
import { providerLabel } from '@/utils/models'

const props = defineProps({
  model: { type: Object, required: true },
  testState: { type: Object, default: () => ({ status: 'idle' }) },
})
defineEmits(['test', 'edit', 'delete'])

const capabilities = computed(() =>
  Object.entries(props.model.capabilities || {}).map(([name, state]) => ({ name, state }))
)

const status = computed(() => {
  const s = props.testState?.status
  if (s === 'testing') return { label: '测试中', cls: 'bg-gray-100 text-gray-500' }
  if (s === 'success') return { label: '已连接', cls: 'bg-green-50 text-green-600' }
  if (s === 'error') return { label: '连接失败', cls: 'bg-red-50 text-red-500' }
  return { label: '未测试', cls: 'bg-gray-100 text-gray-400' }
})
</script>

<template>
  <div class="card p-4">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-sm font-medium text-gray-900">{{ providerLabel(model.provider) }}</p>
        <p class="mt-0.5 truncate font-mono text-xs text-gray-400">{{ model.model }}</p>
      </div>
      <span class="shrink-0 rounded-full px-2 py-0.5 text-xs" :class="status.cls">{{ status.label }}</span>
    </div>

    <p class="mt-3 text-xs text-gray-400">
      <span class="text-gray-500">API Key</span>
      <span class="ml-2 font-mono">{{ model.masked_api_key || '未配置 API Key' }}</span>
    </p>

    <div v-if="capabilities.length" class="mt-3 flex flex-wrap gap-1.5">
      <CapabilityBadge v-for="c in capabilities" :key="c.name" :name="c.name" :state="c.state" />
    </div>

    <p v-if="testState?.status === 'error' && testState.message" class="mt-3 text-xs text-red-500">
      {{ testState.message }}
    </p>
    <p v-else-if="testState?.status === 'success'" class="mt-3 text-xs text-green-600">
      ✓ 连接成功<template v-if="testState.latency_ms != null"> · {{ testState.latency_ms }}ms</template>
    </p>

    <div class="mt-4 flex items-center gap-4 border-t border-gray-50 pt-3">
      <button
        type="button"
        class="text-sm font-medium text-brand-600 disabled:text-gray-300"
        :disabled="testState?.status === 'testing'"
        @click="$emit('test')"
      >
        {{ testState?.status === 'testing' ? '测试中…' : '测试连接' }}
      </button>
      <button type="button" class="text-sm text-gray-500 hover:text-gray-700" @click="$emit('edit')">编辑</button>
      <button type="button" class="ml-auto text-sm text-red-500 hover:text-red-600" @click="$emit('delete')">删除</button>
    </div>
  </div>
</template>
