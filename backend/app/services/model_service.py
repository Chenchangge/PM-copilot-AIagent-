"""AI 模型配置的业务逻辑（CRUD + 连通性测试 + 能力解析）。"""
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.capabilities import Capability, CapabilityState, resolve_capabilities
from app.core.config import settings
from app.core.errors import AIErrorCode
from app.models.ai_model import UserModelConfig
from app.schemas.model import (
    ModelConfigCreate,
    ModelConfigOut,
    ModelConfigUpdate,
    ResolveResult,
    TestConnectionResult,
)
from app.services.model_router import model_router
from app.services.providers import ProviderNotSupportedError, get_adapter, get_embedding_adapter
from app.services.secret_storage import secret_storage


class ModelNotFoundError(Exception):
    pass


class ModelService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _to_out(m: UserModelConfig) -> ModelConfigOut:
        return ModelConfigOut.model_validate(m)

    def list_models(self, user_id: str) -> list[ModelConfigOut]:
        rows = self.db.execute(
            select(UserModelConfig)
            .where(UserModelConfig.user_id == user_id)
            .order_by(UserModelConfig.id)
        ).scalars().all()
        return [self._to_out(r) for r in rows]

    def _get(self, user_id: str, model_id: int) -> UserModelConfig:
        row = self.db.get(UserModelConfig, model_id)
        if row is None or row.user_id != user_id:
            raise ModelNotFoundError()
        return row

    @staticmethod
    def _compute_capabilities(provider: str, model: str, model_type=None) -> dict:
        """能力 = 后端自动推导 + custom 模型的显式用途声明。

        官方 provider 的能力由 resolve_capabilities 自动推导，不受 model_type 影响。
        custom / OpenAI 兼容 provider 的模型名可能不含 "embedding"（如 bge-m3），
        因此允许用户显式声明用途（text_generation / embedding）。
        """
        caps = resolve_capabilities(provider, model)
        if provider == "custom" and model_type is not None:
            if model_type == "embedding":
                caps[Capability.embedding.value] = CapabilityState.supported.value
            elif model_type == "text_generation":
                caps[Capability.text_generation.value] = CapabilityState.supported.value
        return caps

    def create_model(self, user_id: str, data: ModelConfigCreate) -> ModelConfigOut:
        row = UserModelConfig(
            user_id=user_id,
            name=data.name,
            provider=data.provider,
            model=data.model,
            base_url=data.base_url,
            api_key_secret=secret_storage.seal(data.api_key),
            capabilities=self._compute_capabilities(data.provider, data.model, data.model_type),
            enabled=True,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_out(row)

    def get_model(self, user_id: str, model_id: int) -> ModelConfigOut:
        return self._to_out(self._get(user_id, model_id))

    def update_model(self, user_id: str, model_id: int, data: ModelConfigUpdate) -> ModelConfigOut:
        row = self._get(user_id, model_id)
        changes = data.model_dump(exclude_unset=True)
        # model_type 只用于推导 capabilities，不落库（单独处理）
        has_model_type = "model_type" in changes
        model_type = changes.pop("model_type", None)
        if "provider" in changes or "model" in changes or has_model_type:
            new_provider = changes.get("provider", row.provider)
            new_model = changes.get("model", row.model)
            # 未显式传 model_type 且原模型为 embedding：保留 embedding 覆盖
            if model_type is None and not has_model_type and (row.capabilities or {}).get("embedding") == "supported":
                model_type = "embedding"
            row.capabilities = self._compute_capabilities(new_provider, new_model, model_type)
        for key, value in changes.items():
            if key == "api_key":
                row.api_key_secret = secret_storage.seal(value)
            else:
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return self._to_out(row)

    def delete_model(self, user_id: str, model_id: int) -> None:
        row = self._get(user_id, model_id)
        self.db.delete(row)
        self.db.commit()

    def test_connection(self, user_id: str, model_id: int) -> TestConnectionResult:
        row = self._get(user_id, model_id)
        api_key = secret_storage.unseal(row.api_key_secret)
        # Embedding 模型走 /embeddings 测试，其余走 /chat/completions 测试
        if (row.capabilities or {}).get("embedding") == "supported":
            return self._test_embedding_connection(row, api_key)
        return self._test_text_connection(row, api_key)

    def _test_text_connection(self, row: UserModelConfig, api_key: str) -> TestConnectionResult:
        try:
            adapter = get_adapter(row.provider, row.base_url or "", api_key, row.model)
        except ProviderNotSupportedError:
            return TestConnectionResult(
                success=False,
                model=row.model,
                error_code=AIErrorCode.provider_error.value,
                message=f"该 Provider（{row.provider}）暂未支持连接测试。",
            )
        return TestConnectionResult(**adapter.test_connection())

    def _test_embedding_connection(self, row: UserModelConfig, api_key: str) -> TestConnectionResult:
        try:
            adapter = get_embedding_adapter(row.provider, row.base_url or "", api_key, row.model)
        except ProviderNotSupportedError:
            return TestConnectionResult(
                success=False,
                model=row.model,
                error_code=AIErrorCode.provider_error.value,
                message=f"该 Provider（{row.provider}）暂未支持 Embedding 连接测试。",
            )
        return TestConnectionResult(**adapter.test_connection())

    def resolve(self, user_id: str, required_capabilities: list[str]) -> ResolveResult:
        rows = self.db.execute(
            select(UserModelConfig).where(
                UserModelConfig.user_id == user_id,
                UserModelConfig.enabled.is_(True),
            )
        ).scalars().all()
        eligible = model_router.find_models_by_capabilities(rows, required_capabilities)
        models = [self._to_out(m) for m in eligible]
        message = None if models else "没有找到满足当前能力要求的模型"
        return ResolveResult(models=models, message=message)

    def find_embedding_model(self, user_id: str) -> UserModelConfig | None:
        """查找可用的 Embedding 模型（capabilities.embedding == supported）。"""
        rows = self.db.execute(
            select(UserModelConfig).where(
                UserModelConfig.user_id == user_id,
                UserModelConfig.enabled.is_(True),
            )
        ).scalars().all()
        eligible = model_router.find_models_by_capabilities(rows, ["embedding"])
        return eligible[0] if eligible else _server_default_embedding()

    def find_text_generation_model(self, user_id: str) -> UserModelConfig | None:
        """查找支持文本生成的模型（capabilities.text_generation == supported）。"""
        rows = self.db.execute(
            select(UserModelConfig).where(
                UserModelConfig.user_id == user_id,
                UserModelConfig.enabled.is_(True),
            )
        ).scalars().all()
        eligible = model_router.find_models_by_capabilities(rows, ["text_generation"])
        return eligible[0] if eligible else _server_default_llm()

    def find_interview_model(self, user_id: str) -> UserModelConfig | None:
        """查找支持模拟面试的模型（text_generation + reasoning + structured_output）。"""
        rows = self.db.execute(
            select(UserModelConfig).where(
                UserModelConfig.user_id == user_id,
                UserModelConfig.enabled.is_(True),
            )
        ).scalars().all()
        eligible = model_router.find_models_by_capabilities(
            rows, ["text_generation", "reasoning", "structured_output"]
        )
        return eligible[0] if eligible else _server_default_llm()


def _server_default_llm():
    """服务器默认文本生成模型（.env 配置，访客无自有模型时回退）。"""
    if not (settings.default_llm_model and settings.default_llm_api_key):
        return None
    provider = settings.default_llm_provider or "deepseek"
    return SimpleNamespace(
        provider=provider,
        base_url=settings.default_llm_base_url or None,
        model=settings.default_llm_model,
        api_key_secret=settings.default_llm_api_key,
        capabilities=resolve_capabilities(provider, settings.default_llm_model),
    )


def _server_default_embedding():
    """服务器默认 Embedding 模型（.env 配置，访客无自有模型时回退）。"""
    if not (settings.default_embedding_model and settings.default_embedding_api_key):
        return None
    provider = settings.default_embedding_provider or "custom"
    caps = resolve_capabilities(provider, settings.default_embedding_model)
    caps[Capability.embedding.value] = CapabilityState.supported.value
    return SimpleNamespace(
        provider=provider,
        base_url=settings.default_embedding_base_url or None,
        model=settings.default_embedding_model,
        api_key_secret=settings.default_embedding_api_key,
        capabilities=caps,
    )
