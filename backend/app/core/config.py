"""应用配置。

所有配置通过环境变量 / .env 读取，密钥绝不写入代码。
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

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
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 数据库（SQLite）
    database_url: str = "sqlite:///./pm_copilot.db"

    # CORS 允许的前端来源
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
