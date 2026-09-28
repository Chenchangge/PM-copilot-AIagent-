"""DeepSeek Provider Adapter 与配置（单一事实来源）。

DeepSeek 使用 OpenAI 兼容协议，本模块集中定义 DeepSeek 的默认 Base URL、
官方可用模型列表与默认模型，避免模型名散落硬编码在多个地方。

官方兼容端点：{base_url}/chat/completions（无 /v1 前缀，由 OpenAICompatibleAdapter 拼接）。
"""
from app.services.providers.base import OpenAICompatibleAdapter

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 官方可用模型（当前）。deepseek-chat 已废弃，不再作为默认/推荐模型。
DEEPSEEK_MODELS = ["deepseek-flash", "deepseek-v4-pro"]

# 默认模型：deepseek-flash（成本更低、响应更快，适合作为 MVP 默认）。
DEFAULT_DEEPSEEK_MODEL = "deepseek-flash"


class DeepSeekAdapter(OpenAICompatibleAdapter):
    """DeepSeek 适配器：OpenAI 兼容协议 + DeepSeek 默认 Base URL。"""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        super().__init__(
            base_url=base_url or DEFAULT_DEEPSEEK_BASE_URL,
            api_key=api_key,
            model=model,
            provider="deepseek",
        )
