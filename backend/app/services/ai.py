"""DeepSeek AI 客户端占位。

- API Key 只从后端环境变量读取，绝不暴露到前端。
- 当前阶段不实现具体的 AI 调用（问答 / 面试 / 评价）逻辑。
"""
from app.core.config import settings


class DeepSeekClient:
    """DeepSeek 接口封装。具体方法后续实现。"""

    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.deepseek_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


deepseek_client = DeepSeekClient()
