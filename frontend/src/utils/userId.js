// 匿名用户身份：MVP 无登录，首次访问生成匿名 user_id 并存 localStorage。
// 注意：这里只保存匿名 user_id，绝不保存 API Key。

const STORAGE_KEY = 'pm-copilot-user-id'

function generateId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

export function getUserId() {
  let id = null
  try {
    id = localStorage.getItem(STORAGE_KEY)
  } catch {
    return `anon-${generateId()}`
  }
  if (!id) {
    id = `anon-${generateId()}`
    try {
      localStorage.setItem(STORAGE_KEY, id)
    } catch {
      /* localStorage 不可用时忽略 */
    }
  }
  return id
}
