// 知识库 AI 问答接口封装（统一走 service 层，页面不直接 axios）。
import http from './index'

// 调用后端 RAG 问答。MVP 前端只传 query，top_k 默认 5；
// similarity_threshold / max_distance 是 RAG 调参参数，不暴露给普通用户。
export function askKnowledge({ query, top_k = 5, similarity_threshold = null, max_distance = null } = {}) {
  return http.post('/knowledge/qa', {
    query,
    top_k,
    similarity_threshold,
    max_distance,
  })
}

// 知识列表（真实 Markdown 数据源，Step 10）。
export function listKnowledge(params = {}) {
  return http.get('/knowledge', { params })
}

// 知识详情，按 slug / knowledge_id 拉取。
export function getKnowledgeDetail(knowledgeId) {
  return http.get(`/knowledge/${knowledgeId}`)
}

// 重建知识库索引（设置页；需要已配置 Embedding 模型）。
export function reindexKnowledge() {
  return http.post('/knowledge/reindex', {}, { timeout: 180000 })
}
