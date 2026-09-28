"""AI 模型配置的数据模型。"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.masking import mask_secret
from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserModelConfig(Base):
    """用户（匿名）配置的模型信息。

    - api_key_secret 为经 SecretStorage 处理后的值，绝不明文返回给前端。
    - capabilities 由系统根据 provider 推导，用户不可手工修改。
    """

    __tablename__ = "user_model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    api_key_secret: Mapped[str] = mapped_column(String, nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key_secret)

    @property
    def masked_api_key(self) -> str:
        return mask_secret(self.api_key_secret)
