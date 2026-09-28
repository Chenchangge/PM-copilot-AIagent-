<script setup>
import { computed } from 'vue'

import CapabilityBadge from './CapabilityBadge.vue'
import { evaluateCapabilities, providerLabel } from '@/utils/models'

const props = defineProps({
  fn: { type: Object, required: true },
  models: { type: Array, default: () => [] },
  currentModelId: { type: [Number, String], default: null },
})
const emit = defineEmits(['select', 'close', 'add', 'clear'])

const eligibleModels = computed(() =>
  props.models
    .map((model) => ({
      model,
      ...evaluateCapabilities(model.capabilities, props.fn.capabilities),
    }))
    .filter((e) => e.eligible)
)
</script>

<template>
  <div class="fixed inset-0 z-30">
    <div class="absolute inset-0 bg-black/30" @click="$emit('close')"></div>
    <div class="absolute inset-x-0 bottom-0 mx-auto max-w-app rounded-t-2xl bg-white pb-[env(safe-area-inset-bottom)]">
      <div class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
        <p class="text-sm font-semibold text-gray-900">为「{{ fn.label }}」选择模型</p>
        <button type="button" class="text-sm text-gray-400 hover:text-gray-600" @click="$emit('close')">取消</button>
      </div>

      <div class="max-h-[65vh] overflow-y-auto px-5 py-4">
        <p class="text-xs text-gray-400">所需能力：{{ fn.description }}</p>

        <!-- 无符合模型 -->
        <div v-if="!eligibleModels.length" class="py-10 text-center">
          <p class="text-sm font-medium text-gray-900">暂无符合要求的模型</p>
          <p class="mt-1 text-sm text-gray-400">当前没有满足该功能能力的模型。</p>
          <button type="button" class="mt-4 text-sm font-medium text-brand-600" @click="$emit('add')">去添加模型</button>
        </div>

        <!-- 模型列表 -->
        <div v-else class="mt-3 space-y-2">
          <button
            v-for="e in eligibleModels"
            :key="e.model.id"
            type="button"
            class="card block w-full p-4 text-left transition-colors"
            :class="e.model.id === currentModelId ? 'border-brand-300' : 'hover:border-gray-200'"
            @click="$emit('select', e.model.id)"
          >
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-900">
                {{ providerLabel(e.model.provider) }}
                <span class="ml-1 font-mono text-xs text-gray-400">{{ e.model.model }}</span>
              </p>
              <span v-if="e.model.id === currentModelId" class="text-xs font-medium text-brand-600">当前使用</span>
            </div>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <CapabilityBadge
                v-for="cap in fn.capabilities"
                :key="cap"
                :name="cap"
                :state="(e.model.capabilities && e.model.capabilities[cap]) || 'unknown'"
              />
            </div>
            <p v-if="e.hasUnknown" class="mt-2 text-xs text-amber-500">支持情况未知，建议先测试连接</p>
          </button>
        </div>

        <!-- 清除选择 -->
        <button
          v-if="currentModelId != null"
          type="button"
          class="mt-4 w-full rounded-2xl border border-gray-200 py-3 text-sm text-gray-500 active:bg-gray-50"
          @click="$emit('clear')"
        >
          清除当前选择
        </button>
      </div>
    </div>
  </div>
</template>
