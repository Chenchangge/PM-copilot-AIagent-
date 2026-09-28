// 模拟面试前端辅助：错误码提取与「去配置模型」引导。

// 需要引导用户去「AI 模型 / API」配置页的错误码
const MODEL_CONFIG_ERRORS = new Set(['INTERVIEW_MODEL_NOT_FOUND'])

export function needsModelConfig(code) {
  return !!code && MODEL_CONFIG_ERRORS.has(code)
}

// 从 axios 错误中提取 { code, message }。
// 优先使用后端统一错误格式 { error: { code, message } }；其余回退 FastAPI 422 / 通用文案。
// 绝不放行 traceback / API Key / 内部路径到页面。
export function extractInterviewError(e) {
  const body = e?.response?.data
  if (body?.error) {
    return {
      code: body.error.code || null,
      message: body.error.message || '请求失败，请稍后重试。',
    }
  }
  const detail = body?.detail
  if (typeof detail === 'string') return { code: null, message: detail }
  if (Array.isArray(detail) && detail.length) {
    return { code: null, message: detail[0]?.msg || '请求失败，请稍后重试。' }
  }
  return { code: null, message: '请求失败，请稍后重试。' }
}
