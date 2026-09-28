"""应用配置。

所有配置通过环境变量 / .env 读取，密钥绝不写入代码。
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.providers.deepseek import DEFAULT_DEEPSEEK_BASE_URL, DEFAULT_DEEPSEEK_MODEL

# 项目根目录（pm-copilot/），.env 位于根目录
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_name: str = "PM Copilot"
    environment: str = "development"

    # DeepSeek AI（API Key 仅从后端环境变量读取，不暴露到前端）
    # Base URL / 默认模型以 providers/deepseek.py 为单一事实来源
    deepseek_api_key: str = ""
    deepseek_base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    deepseek_model: str = DEFAULT_DEEPSEEK_MODEL

    # 数据库（SQLite）
    database_url: str = "sqlite:///./pm_copilot.db"

    # 密钥加密主密钥（TODO：当前 SecretStorage 为透传占位，尚未启用真实加密）
    secret_encryption_key: str = ""

    # RAG / 向量库（Chroma）
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "pm_copilot_knowledge"

    # CORS 允许的前端来源
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # 服务器默认模型（访客无自有配置时回退，用于简历演示等场景；留空=不启用）
    default_llm_provider: str = ""
    default_llm_base_url: str = ""
    default_llm_model: str = ""
    default_llm_api_key: str = ""
    default_embedding_provider: str = ""
    default_embedding_base_url: str = ""
    default_embedding_model: str = ""
    default_embedding_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
