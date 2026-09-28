"""Provider Adapter 抽象与 OpenAI 兼容协议的通用实现。"""
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.errors import AIErrorCode, FRIENDLY_MESSAGES

DEFAULT_TIMEOUT_SECONDS = 15.0


class BaseModelAdapter(ABC):
    """统一的模型调用接口抽象。所有 Provider Adapter 实现此接口。"""

    def __init__(self, base_url: str, api_key: str, model: str, provider: str) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model
        self.provider = provider

    def classify_error(self, exc: Exception) -> tuple[str, str]:
        """把 Provider 异常映射为统一错误码 + 友好信息。默认 UNKNOWN，子类可覆盖。"""
        return AIErrorCode.unknown.value, FRIENDLY_MESSAGES[AIErrorCode.unknown.value]

    @abstractmethod
    def test_connection(self) -> dict:
        """测试连通性，返回 TestConnectionResult 结构。"""

    @abstractmethod
    def generate(self, messages: list[dict[str, Any]], options: dict[str, Any] | None = None) -> dict:
        """统一生成接口，返回统一格式。"""


class OpenAICompatibleAdapter(BaseModelAdapter):
    """OpenAI 兼容协议（/chat/completions）的通用适配器。

    覆盖 DeepSeek / OpenAI / 其他兼容 OpenAI API 的 provider。
    """

    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _status_to_code(status: int) -> str:
        if status in (401, 403):
            return AIErrorCode.invalid_api_key.value
        if status == 404:
            return AIErrorCode.model_not_found.value
        if status == 429:
            return AIErrorCode.rate_limited.value
        if 400 <= status < 500:
            return AIErrorCode.invalid_base_url.value
        return AIErrorCode.provider_error.value

    def classify_error(self, exc: Exception) -> tuple[str, str]:
        if isinstance(exc, httpx.TimeoutException):
            code = AIErrorCode.timeout.value
        elif isinstance(exc, httpx.HTTPStatusError):
            code = self._status_to_code(exc.response.status_code)
        elif isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
            code = AIErrorCode.network_error.value
        else:
            code = AIErrorCode.unknown.value
        return code, FRIENDLY_MESSAGES[code]

    def test_connection(self) -> dict:
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                resp = client.post(
                    self._endpoint(),
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                    },
                )
                resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - 统一归类，不向用户泄漏第三方细节
            code, message = self.classify_error(exc)
            return {
                "success": False,
                "model": self.model,
                "latency_ms": None,
                "error_code": code,
                "message": message,
            }
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "success": True,
            "model": self.model,
            "latency_ms": latency_ms,
            "error_code": None,
            "message": None,
        }

    def generate(self, messages: list[dict[str, Any]], options: dict[str, Any] | None = None) -> dict:
        options = options or {}
        payload = {"model": self.model, "messages": messages, **options}
        start = time.perf_counter()
        with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            resp = client.post(self._endpoint(), headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.perf_counter() - start) * 1000)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        usage = data.get("usage") or {}
        return {
            "content": message.get("content"),
            "model": data.get("model") or self.model,
            "provider": self.provider,
            "usage": {
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
            "latency_ms": latency_ms,
        }
