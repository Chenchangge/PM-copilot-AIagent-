"""Embedding Adapter：与 Text Generation 并列，复用 Provider / Model 体系。

- BaseEmbeddingAdapter 是统一抽象（embed(texts) -> list[list[float]]）。
- OpenAICompatibleEmbeddingAdapter 调用 OpenAI 兼容的 /embeddings 接口，内部按固定
  batch 分批调用，并对响应做数量 / 维度校验，保证向量与输入一一对应、顺序一致。
- MockEmbeddingAdapter 生成确定性哈希向量，仅用于测试 / 无真实 Key 时的 Pipeline 验证。

注意：不要把「文本生成模型」误当成 Embedding 模型；DeepSeek 不提供 Embedding 接口，
故 get_embedding_adapter 仅支持 openai / custom（OpenAI 兼容）。
"""
import hashlib
import math
import re
import time
from abc import ABC, abstractmethod

import httpx

from app.core.errors import AIErrorCode, FRIENDLY_MESSAGES

# 单次 /embeddings 请求的最大输入文本数。
#
# 知识库约 270 个 chunk（平均 ~152 字符、最大 ~346 字符）。若一次性全部提交，会超过
# 多数 Provider 的单请求 input/token 上限。取固定 10：这是阿里云百炼（DashScope）
# 兼容端点「单请求最多 10 个 input」的硬上限，同时兼容 OpenAI（上限更高）等其余
# OpenAI-compatible provider，避免为适配各 Provider 引入 tokenizer。
# 构造时可被 batch_size 覆盖。
DEFAULT_EMBEDDING_BATCH_SIZE = 10


class EmbeddingResponseError(Exception):
    """Embedding 响应结构非法（字段缺失 / 数量不匹配 / 维度不一致）。"""


class BaseEmbeddingAdapter(ABC):
    def __init__(self, provider: str, model: str, base_url: str, api_key: str) -> None:
        self.provider = provider
        self.model = model
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """返回与输入一一对应的向量列表。"""


class OpenAICompatibleEmbeddingAdapter(BaseEmbeddingAdapter):
    """OpenAI 兼容 /embeddings 接口适配器。

    分批调用，并对每一批响应做校验：
    - data 字段存在且为列表；
    - 返回向量数量 == 请求文本数量；
    - 向量维度在批内 / 跨批一致。

    任何一批失败或校验不通过都会抛异常（不返回部分结果），由上层决定整体失败。
    """

    def __init__(
        self,
        provider: str,
        model: str,
        base_url: str,
        api_key: str,
        batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    ) -> None:
        super().__init__(provider, model, base_url, api_key)
        self.batch_size = batch_size

    def _endpoint(self) -> str:
        return f"{self.base_url}/embeddings"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        dimension: int | None = None
        with httpx.Client(timeout=60.0) as client:
            for start in range(0, len(texts), self.batch_size):
                batch = texts[start : start + self.batch_size]
                batch_vectors, batch_dimension = self._embed_batch(client, batch)
                if dimension is None:
                    dimension = batch_dimension
                elif batch_dimension != dimension:
                    raise EmbeddingResponseError(
                        f"Embedding 维度不一致：{dimension} vs {batch_dimension}"
                    )
                vectors.extend(batch_vectors)
        # 防御：最终数量必须与输入一致（顺序由分片循环 + 响应顺序共同保证）
        if len(vectors) != len(texts):
            raise EmbeddingResponseError(f"Embedding 数量不匹配：{len(vectors)} vs {len(texts)}")
        return vectors

    def _embed_batch(self, client: httpx.Client, texts: list[str]) -> tuple[list[list[float]], int]:
        resp = client.post(
            self._endpoint(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": texts},
        )
        resp.raise_for_status()
        return self._parse_response(resp.json(), len(texts))

    @staticmethod
    def _parse_response(data, expected_count: int) -> tuple[list[list[float]], int]:
        """解析并校验单批响应，返回 (向量列表, 维度)。数量 / 维度不符则抛异常。"""
        if not isinstance(data, dict):
            raise EmbeddingResponseError("Embedding 响应不是 JSON 对象")
        items = data.get("data")
        if not isinstance(items, list):
            raise EmbeddingResponseError("Embedding 响应缺少 data 列表")
        if len(items) != expected_count:
            raise EmbeddingResponseError(
                f"Embedding 数量不匹配：请求 {expected_count}，返回 {len(items)}"
            )
        vectors: list[list[float]] = []
        dimension: int | None = None
        for item in items:
            if not isinstance(item, dict):
                raise EmbeddingResponseError("Embedding 响应项格式非法")
            vec = item.get("embedding")
            if not isinstance(vec, list) or not vec:
                raise EmbeddingResponseError("Embedding 响应项缺少向量")
            if dimension is None:
                dimension = len(vec)
            elif len(vec) != dimension:
                raise EmbeddingResponseError("同一响应内向量维度不一致")
            vectors.append(vec)
        return vectors, dimension

    def test_connection(self) -> dict:
        """真实调用 /embeddings 做连通性测试，返回 TestConnectionResult 结构。

        与文本生成 adapter 一致：失败只返回统一错误码 + 友好信息，不泄漏 Key / 第三方异常。
        """
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    self._endpoint(),
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model, "input": ["ping"]},
                )
                resp.raise_for_status()
                self._parse_response(resp.json(), 1)
        except Exception as exc:  # noqa: BLE001 - 统一归类，不泄漏第三方细节
            code = self._classify_error(exc)
            return {
                "success": False,
                "model": self.model,
                "latency_ms": None,
                "error_code": code,
                "message": FRIENDLY_MESSAGES[code],
            }
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "success": True,
            "model": self.model,
            "latency_ms": latency_ms,
            "error_code": None,
            "message": None,
        }

    @staticmethod
    def _classify_error(exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return AIErrorCode.timeout.value
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if status in (401, 403):
                return AIErrorCode.invalid_api_key.value
            if status == 404:
                return AIErrorCode.model_not_found.value
            if status == 429:
                return AIErrorCode.rate_limited.value
            if 400 <= status < 500:
                return AIErrorCode.invalid_base_url.value
            return AIErrorCode.provider_error.value
        if isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
            return AIErrorCode.network_error.value
        return AIErrorCode.provider_error.value  # EmbeddingResponseError / 其他


class MockEmbeddingAdapter(BaseEmbeddingAdapter):
    """确定性哈希向量（384 维）。仅用于测试，非真实语义 Embedding。"""

    dim = 384

    def __init__(self) -> None:
        super().__init__(provider="mock", model="mock-embedding-384d", base_url="", api_key="")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"\w+", text.lower())
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
