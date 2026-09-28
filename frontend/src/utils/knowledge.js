// 知识相关前端辅助：分类/主题/难度中文标签、RAG QA 错误友好提示、来源跳转。

// 知识一级分类 slug → 中文标签（与 backend/app/learning/constants.py 的 11 分类一致）
export const KNOWLEDGE_CATEGORY_LABELS = {
  'product-foundation': '产品基础',
  'user-research': '用户研究',
  'product-design': '产品设计',
  'data-analysis': '数据分析',
  'user-growth': '用户增长',
  commercialization: '商业化',
  'strategy-product': '策略产品',
  'b2b-enterprise': 'B端/企业产品',
  'ai-product': 'AI产品',
  'project-collaboration': '项目管理与协作',
  'interview-job': '面试与求职',
}

export function getKnowledgeCategoryLabel(category) {
  return KNOWLEDGE_CATEGORY_LABELS[category] || category || ''
}

// 知识二级主题 slug → 中文标签（KnowledgeCategory → KnowledgeTopic → KnowledgePoint 三级结构）
export const KNOWLEDGE_TOPIC_LABELS = {
  'pm-basics': '产品经理基础',
  'requirements-value': '需求与价值',
  'research-basics': '用户研究基础',
  'requirements-doc': '需求文档',
  'ia-flow': '信息架构与流程',
  interaction: '交互设计',
  'core-metrics': '核心指标',
  'analysis-methods': '分析方法',
  experimentation: '实验方法',
  'data-tools': '数据工具',
  'business-model': '商业模式',
  'llm-basics': '大模型基础',
  'rag-retrieval': 'RAG与检索',
  'prompt-agent': 'Prompt与Agent',
  'eval-reliability': '评测与可靠性',
  'project-tools': '项目管理工具',
  'self-introduction': '自我介绍',
  'interview-frameworks': '答题框架',
}

export function getKnowledgeTopicLabel(topic) {
  return KNOWLEDGE_TOPIC_LABELS[topic] || topic || ''
}

export const KNOWLEDGE_DIFFICULTY_LABELS = {
  beginner: '入门',
  intermediate: '进阶',
  advanced: '高级',
}

export function getKnowledgeDifficultyLabel(difficulty) {
  return KNOWLEDGE_DIFFICULTY_LABELS[difficulty] || difficulty || ''
}

// RAG QA 来源卡片跳转目标：knowledge_id（slug）→ 知识详情路由；无 id 则不可跳转。
export function sourceDetailPath(source) {
  return source?.knowledge_id ? `/learning/knowledge/${source.knowledge_id}` : ''
}

// 需要引导用户去「AI 模型 / API」配置页的 RAG QA 错误码
const QA_MODEL_CONFIG_ERRORS = new Set(['EMBEDDING_MODEL_NOT_FOUND', 'LLM_MODEL_NOT_FOUND'])

export function needsModelConfig(code) {
  return !!code && QA_MODEL_CONFIG_ERRORS.has(code)
}

// 后端无 message 时的兜底文案（后端通常已返回友好 message，此仅兜底）
const QA_ERROR_FALLBACKS = {
  EMBEDDING_MODEL_NOT_FOUND: '知识问答功能需要先配置一个支持知识检索的模型',
  LLM_MODEL_NOT_FOUND: '知识问答功能需要先配置一个支持文本生成的模型',
  INDEX_NOT_FOUND: '知识库索引尚未构建',
  INDEX_MODEL_MISMATCH: '知识库索引与当前模型不一致，请重建',
}

export function errorMessageFor(code, backendMessage) {
  if (backendMessage) return backendMessage
  return QA_ERROR_FALLBACKS[code] || '请求失败，请稍后重试。'
}
