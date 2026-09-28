"""AI 模型配置相关的 Pydantic Schema。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# 模型用途（仅对 custom / OpenAI 兼容 provider 生效，用于显式声明能力）。
# 官方 provider（deepseek/openai/claude/gemini）的能力仍由后端自动推导，不受此字段影响。
ModelType = Literal["text_generation", "embedding"]


class ModelConfigCreate(BaseModel):
    name: str
    provider: str
    model: str
    base_url: str | None = None
    api_key: str  # 完整 Key 仅在请求体接收，服务端处理后不再明文暴露
    model_type: ModelType | None = None


class ModelConfigUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_type: ModelType | None = None


class ModelConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    name: str
    provider: str
    model: str
    base_url: str | None
    has_api_key: bool
    masked_api_key: str
    capabilities: dict[str, str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class TestConnectionResult(BaseModel):
    success: bool
    model: str | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    message: str | None = None


class ResolveRequest(BaseModel):
    required_capabilities: list[str]


class ResolveResult(BaseModel):
    models: list[ModelConfigOut] = Field(default_factory=list)
    message: str | None = None
