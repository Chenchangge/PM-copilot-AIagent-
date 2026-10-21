// 学习计划接口封装（统一走 service 层，页面不直接 axios）。
import http from './index'

export function getLearningTaxonomy() {
  return http.get('/learning/taxonomy')
}

// 学习计划页专用：scope=plan 只下发路径卡 / 精简分类 / 分组专题，不含 640 个标签。
export function getPlanTaxonomy(params = {}) {
  return http.get('/learning/taxonomy', { params: { scope: 'plan', ...params } })
}

export function estimatePlan(data) {
  return http.post('/learning/plans/estimate', data)
}

export function createPlan(data) {
  return http.post('/learning/plans', data)
}

export function listPlans() {
  return http.get('/learning/plans')
}

export function getPlan(id) {
  return http.get(`/learning/plans/${id}`)
}

export function pausePlan(id) {
  return http.post(`/learning/plans/${id}/pause`)
}

export function resumePlan(id) {
  return http.post(`/learning/plans/${id}/resume`)
}

export function updatePlan(id, data) {
  return http.patch(`/learning/plans/${id}`, data)
}

export function startTask(id) {
  return http.post(`/learning/tasks/${id}/start`)
}

export function completeTask(id) {
  return http.post(`/learning/tasks/${id}/complete`)
}

export function skipTask(id) {
  return http.post(`/learning/tasks/${id}/skip`)
}

export function makeupPlan(id) {
  return http.post(`/learning/plans/${id}/makeup`)
}

export function startKnowledge(id) {
  return http.post(`/learning/knowledge/${id}/start`)
}

export function completeKnowledge(id) {
  return http.post(`/learning/knowledge/${id}/complete`)
}

export function getHomeSummary() {
  return http.get('/learning/home-summary')
}
