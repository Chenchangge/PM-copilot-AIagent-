"""Provider Adapter 工厂。

架构：ModelService → get_adapter() → Provider Adapter → 具体模型 API。
不把调用逻辑写死在某个 Provider 上。
"""
from app.services.providers.base import BaseModelAdapter, OpenAICompatibleAdapter
from app.services.providers.deepseek import DeepSeekAdapter
from app.services.providers.embedding import (
    BaseEmbeddingAdapter,
    MockEmbeddingAdapter,
    OpenAICompatibleEmbeddingAdapter,
)

# 使用 OpenAI 兼容协议的 provider（同一套 /chat/completions）
_OPENAI_COMPATIBLE_PROVIDERS = {"deepseek", "openai", "custom"}
# 提供 Embedding 的 provider（OpenAI 兼容 /embeddings）。DeepSeek 不提供 Embedding。
_EMBEDDING_PROVIDERS = {"openai", "custom"}


class ProviderNotSupportedError(Exception):
    def __init__(self, provider: str) -> None:
        self.provider = provider
        super().__init__(f"provider 暂未支持: {provider}")


def get_adapter(provider: str, base_url: str, api_key: str, model: str) -> BaseModelAdapter:
    """根据 provider 返回对应文本生成 Adapter；未接入的 provider 抛出 ProviderNotSupportedError。"""
    if provider == "deepseek":
        return DeepSeekAdapter(base_url, api_key, model)
    if provider in _OPENAI_COMPATIBLE_PROVIDERS:
        return OpenAICompatibleAdapter(base_url, api_key, model, provider=provider)
    raise ProviderNotSupportedError(provider)


def get_embedding_adapter(provider: str, base_url: str, api_key: str, model: str) -> BaseEmbeddingAdapter:
    """根据 provider 返回对应 Embedding Adapter。仅支持明确提供 Embedding 的 provider。"""
    if provider in _EMBEDDING_PROVIDERS:
        return OpenAICompatibleEmbeddingAdapter(provider, model, base_url, api_key)
    raise ProviderNotSupportedError(provider)


__all__ = [
    "BaseModelAdapter",
    "OpenAICompatibleAdapter",
    "DeepSeekAdapter",
    "BaseEmbeddingAdapter",
    "OpenAICompatibleEmbeddingAdapter",
    "MockEmbeddingAdapter",
    "ProviderNotSupportedError",
    "get_adapter",
    "get_embedding_adapter",
]
