"""统一的 AI 错误分类。

前端仅根据 error_code 展示友好提示；绝不把第三方 Provider 的原始错误、
堆栈或请求头返回给用户。
"""
from enum import Enum


class AIErrorCode(str, Enum):
    invalid_api_key = "INVALID_API_KEY"
    model_not_found = "MODEL_NOT_FOUND"
    invalid_base_url = "INVALID_BASE_URL"
    timeout = "TIMEOUT"
    rate_limited = "RATE_LIMITED"
    provider_error = "PROVIDER_ERROR"
    network_error = "NETWORK_ERROR"
    unknown = "UNKNOWN"


FRIENDLY_MESSAGES: dict[str, str] = {
    AIErrorCode.invalid_api_key.value: "API Key 无效，请检查配置。",
    AIErrorCode.model_not_found.value: "未找到该 Model，请检查 Model 名称。",
    AIErrorCode.invalid_base_url.value: "无法连接模型服务，请检查 Base URL。",
    AIErrorCode.timeout.value: "连接超时，请稍后重试。",
    AIErrorCode.rate_limited.value: "请求过于频繁，请稍后重试。",
    AIErrorCode.provider_error.value: "模型服务返回错误，请稍后重试。",
    AIErrorCode.network_error.value: "网络连接失败，请检查网络或 Base URL。",
    AIErrorCode.unknown.value: "连接失败，请检查配置后重试。",
}
