// AI 模型 / API 页面相关的常量与工具。
// 能力由后端 Capability Registry 决定，前端只负责展示，不允许用户手工修改。

import { getUserId } from './userId'

// 能力 key → 中文名（对应后端 capabilities 字段）
export const CAPABILITY_LABELS = {
  text_generation: '文本生成',
  reasoning: '推理',
  structured_output: '结构化输出',
  multimodal_understanding: '多模态理解',
  image_generation: '图像生成',
  embedding: 'Embedding',
}

// 能力状态展示元数据
export const CAPABILITY_STATE_META = {
  supported: { icon: '✓', label: '支持', text: 'text-green-600', border: 'border-green-100 bg-green-50' },
  unsupported: { icon: '✕', label: '不支持', text: 'text-gray-400', border: 'border-gray-100 bg-gray-50' },
  unknown: { icon: '?', label: '未知', text: 'text-gray-400', border: 'border-gray-200 bg-white' },
}

// Provider 选项（value 与后端一致）
export const PROVIDER_OPTIONS = [
  { value: 'deepseek', label: 'DeepSeek', baseUrl: 'https://api.deepseek.com', model: 'deepseek-flash' },
  { value: 'openai', label: 'OpenAI', baseUrl: 'https://api.openai.com/v1', model: '' },
  { value: 'claude', label: 'Claude', baseUrl: '', model: '' },
  { value: 'gemini', label: 'Gemini', baseUrl: '', model: '' },
  { value: 'custom', label: '自定义 OpenAI Compatible', baseUrl: '', model: '' },
]

// 模型用途（仅对 custom / OpenAI 兼容 provider 生效，用于显式声明能力）
export const MODEL_TYPE_OPTIONS = [
  { value: 'text_generation', label: '文本生成' },
  { value: 'embedding', label: 'Embedding' },
]

export function providerLabel(value) {
  const found = PROVIDER_OPTIONS.find((p) => p.value === value)
  return found ? found.label : value
}

// 功能 → 所需能力（能力要求与后端实际解析一致）
export const FUNCTION_DEFINITIONS = [
  { id: 'knowledge_qa', label: '知识问答', capabilities: ['text_generation', 'embedding'], description: '文本生成 · 知识检索' },
  { id: 'mock_interview', label: '模拟面试', capabilities: ['text_generation', 'reasoning', 'structured_output'], description: '文本生成 · 推理 · 结构化输出' },
  { id: 'evaluation', label: '面试评价', capabilities: ['text_generation', 'reasoning', 'structured_output'], description: '文本生成 · 推理 · 结构化输出' },
  { id: 'embedding', label: '知识检索', capabilities: ['embedding'], description: '知识库检索（知识问答需要）' },
]

// 连接测试错误码 → 友好提示（优先使用后端返回的 message，此处作为兜底）
export const ERROR_MESSAGES = {
  INVALID_API_KEY: 'API Key 无效，请检查配置。',
  MODEL_NOT_FOUND: '未找到该 Model，请检查 Model 名称。',
  INVALID_BASE_URL: '无法连接模型服务，请检查 Base URL。',
  TIMEOUT: '连接超时，请稍后重试。',
  RATE_LIMITED: '请求过于频繁，请稍后重试。',
  PROVIDER_ERROR: '模型服务返回错误，请稍后重试。',
  NETWORK_ERROR: '网络连接失败，请检查网络或 Base URL。',
  UNKNOWN: '连接失败，请检查配置后重试。',
}

// 判断模型是否满足某功能的能力要求：
// - 任一必需能力为 unsupported → 不可用
// - 全部为 supported → 可用
// - 含 unknown → 可用但需提示「支持情况未知」
export function evaluateCapabilities(capabilities, required) {
  if (!required || required.length === 0) return { eligible: true, hasUnknown: false }
  let hasUnknown = false
  for (const cap of required) {
    const state = (capabilities && capabilities[cap]) || 'unknown'
    if (state === 'unsupported') return { eligible: false, hasUnknown: false }
    if (state === 'unknown') hasUnknown = true
  }
  return { eligible: true, hasUnknown }
}

// ---- 功能 → 模型绑定（最小可用方案：localStorage，按匿名 user_id 隔离）----
function bindingKey() {
  return `pm-copilot-model-bindings:${getUserId()}`
}

export function getBindings() {
  try {
    return JSON.parse(localStorage.getItem(bindingKey())) || {}
  } catch {
    return {}
  }
}

export function setBinding(functionId, modelId) {
  const bindings = getBindings()
  if (modelId == null) {
    delete bindings[functionId]
  } else {
    bindings[functionId] = modelId
  }
  try {
    localStorage.setItem(bindingKey(), JSON.stringify(bindings))
  } catch {
    /* ignore */
  }
}

export function removeBindingsForModel(modelId) {
  const bindings = getBindings()
  let changed = false
  for (const [fn, id] of Object.entries(bindings)) {
    if (id === modelId) {
      delete bindings[fn]
      changed = true
    }
  }
  if (changed) {
    try {
      localStorage.setItem(bindingKey(), JSON.stringify(bindings))
    } catch {
      /* ignore */
    }
  }
}
