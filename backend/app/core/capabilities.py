"""AI 能力抽象（与 PRD 8.1 对齐）。

能力由系统根据 provider + model 推导，不允许用户手工勾选。
无法确认的能力标记为 unknown，不凭空声称支持/不支持。
"""
from enum import Enum


class Capability(str, Enum):
    text_generation = "text_generation"
    reasoning = "reasoning"
    structured_output = "structured_output"
    multimodal_understanding = "multimodal_understanding"
    image_generation = "image_generation"
    embedding = "embedding"


class CapabilityState(str, Enum):
    supported = "supported"
    unsupported = "unsupported"
    unknown = "unknown"


ALL_CAPABILITIES = [c.value for c in Capability]


# 已知 provider 的能力预设。只记录有依据的结论，无法确认的用 unknown。
# 后续接入新 provider 时在此登记，或改由 Provider Adapter 提供。
PROVIDER_CAPABILITY_PRESETS: dict[str, dict[str, str]] = {
    "deepseek": {
        Capability.text_generation.value: CapabilityState.supported.value,
        Capability.reasoning.value: CapabilityState.supported.value,
        Capability.structured_output.value: CapabilityState.supported.value,
        Capability.multimodal_understanding.value: CapabilityState.unsupported.value,
        Capability.image_generation.value: CapabilityState.unsupported.value,
        Capability.embedding.value: CapabilityState.unknown.value,
    },
}


def _is_embedding_model(provider: str, model_lower: str) -> bool:
    """判断模型是否明确提供 embedding，依据 provider 的已知规则，不凭空声称。

    - OpenAI：有明确的 embedding 模型命名（text-embedding-*）。
    - 其他（含 custom）：仅当模型名明确含 "embedding" 才视为支持，不假设所有模型都支持。
    """
    if provider == "openai":
        return model_lower.startswith("text-embedding")
    return "embedding" in model_lower


def resolve_capabilities(provider: str, model: str = "") -> dict[str, str]:
    """根据 provider 推导能力集合；未登记的 provider 返回全 unknown。

    embedding 能力按 provider 的已知模型规则推导（见 _is_embedding_model）。
    """
    preset = PROVIDER_CAPABILITY_PRESETS.get(provider)
    caps = dict(preset) if preset else {c: CapabilityState.unknown.value for c in ALL_CAPABILITIES}
    if _is_embedding_model(provider, (model or "").lower()):
        caps[Capability.embedding.value] = CapabilityState.supported.value
    return caps
