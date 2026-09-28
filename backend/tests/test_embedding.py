"""Embedding Adapter 单元测试（mock httpx，不发起真实网络请求）。

覆盖：batching 分批 / 顺序保持 / 数量校验 / 维度一致性 / 响应字段校验 / 工厂路由。
"""
import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.services.providers import (
    OpenAICompatibleEmbeddingAdapter,
    ProviderNotSupportedError,
    get_embedding_adapter,
)
from app.services.providers.embedding import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    EmbeddingResponseError,
)


def _adapter(batch_size=DEFAULT_EMBEDDING_BATCH_SIZE):
    return OpenAICompatibleEmbeddingAdapter(
        "openai", "text-embedding-3-small", "https://api.openai.com/v1", "sk-test", batch_size=batch_size
    )


def _req():
    return httpx.Request("POST", "https://api.openai.com/v1/embeddings")


def _response(vectors):
    """把向量列表包装成 OpenAI /embeddings 响应（顺序与列表一致）。"""
    return httpx.Response(
        200,
        request=_req(),
        json={"object": "list", "data": [{"embedding": v} for v in vectors]},
    )


def _patch_client(responses):
    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    client.post.side_effect = responses if isinstance(responses, list) else [responses]
    return patch("app.services.providers.embedding.httpx.Client", return_value=client), client


class TestBatching(unittest.TestCase):
    def test_single_batch(self):
        texts = ["a", "b", "c"]
        p, client = _patch_client(_response([[0.1] * 8, [0.2] * 8, [0.3] * 8]))
        with p:
            vecs = _adapter().embed(texts)
        self.assertEqual(len(vecs), 3)
        self.assertEqual(client.post.call_count, 1)

    def test_batching_splits_and_preserves_order(self):
        adapter = _adapter(batch_size=2)
        texts = ["apple", "banana", "cherry", "date", "elderberry"]

        def side_effect(*args, **kwargs):
            inputs = kwargs["json"]["input"]
            # 每个向量用输入首字符可辨识，便于验证合并后的顺序
            return _response([[float(ord(t[0]))] for t in inputs])

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.post.side_effect = side_effect
        with patch("app.services.providers.embedding.httpx.Client", return_value=client):
            vecs = adapter.embed(texts)
        self.assertEqual(len(vecs), 5)
        self.assertEqual(client.post.call_count, 3)  # ceil(5 / 2)
        for text, vec in zip(texts, vecs):
            self.assertEqual(vec[0], float(ord(text[0])))

    def test_empty_texts(self):
        self.assertEqual(_adapter().embed([]), [])


class TestResponseValidation(unittest.TestCase):
    def test_count_mismatch_raises(self):
        # 请求 3 条，返回 2 条
        p, _ = _patch_client(_response([[1.0] * 8, [2.0] * 8]))
        with p:
            with self.assertRaises(EmbeddingResponseError):
                _adapter().embed(["a", "b", "c"])

    def test_missing_data_raises(self):
        resp = httpx.Response(200, request=_req(), json={"foo": "bar"})
        p, _ = _patch_client(resp)
        with p:
            with self.assertRaises(EmbeddingResponseError):
                _adapter().embed(["a"])

    def test_missing_embedding_field_raises(self):
        resp = httpx.Response(200, request=_req(), json={"data": [{"index": 0}]})
        p, _ = _patch_client(resp)
        with p:
            with self.assertRaises(EmbeddingResponseError):
                _adapter().embed(["a"])

    def test_dimension_mismatch_within_batch_raises(self):
        p, _ = _patch_client(_response([[1.0] * 8, [1.0] * 16]))
        with p:
            with self.assertRaises(EmbeddingResponseError):
                _adapter().embed(["a", "b"])

    def test_dimension_mismatch_across_batches_raises(self):
        adapter = _adapter(batch_size=2)
        r1 = _response([[1.0] * 8, [1.0] * 8])
        r2 = _response([[1.0] * 16, [1.0] * 16])
        p, _ = _patch_client([r1, r2])
        with p:
            with self.assertRaises(EmbeddingResponseError):
                adapter.embed(["a", "b", "c", "d"])

    def test_http_error_propagates(self):
        exc = httpx.HTTPStatusError("401", request=_req(), response=httpx.Response(401, request=_req()))
        p, _ = _patch_client(exc)
        with p:
            with self.assertRaises(httpx.HTTPStatusError):
                _adapter().embed(["a"])


class TestFactory(unittest.TestCase):
    def test_openai_returns_compatible_adapter(self):
        adapter = get_embedding_adapter("openai", "https://api.openai.com/v1", "sk", "text-embedding-3-small")
        self.assertIsInstance(adapter, OpenAICompatibleEmbeddingAdapter)

    def test_custom_returns_compatible_adapter(self):
        adapter = get_embedding_adapter("custom", "https://x/v1", "sk", "text-embedding-v3")
        self.assertIsInstance(adapter, OpenAICompatibleEmbeddingAdapter)

    def test_deepseek_not_supported(self):
        with self.assertRaises(ProviderNotSupportedError):
            get_embedding_adapter("deepseek", "https://api.deepseek.com", "sk", "deepseek-flash")


class TestConnection(unittest.TestCase):
    def test_connection_success(self):
        p, _ = _patch_client(_response([[1.0] * 8]))
        with p:
            result = _adapter().test_connection()
        self.assertTrue(result["success"])
        self.assertIsNone(result["error_code"])
        self.assertIsNotNone(result["latency_ms"])

    def test_connection_invalid_key(self):
        exc = httpx.HTTPStatusError("401", request=_req(), response=httpx.Response(401, request=_req()))
        p, _ = _patch_client(exc)
        with p:
            result = _adapter().test_connection()
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "INVALID_API_KEY")
        self.assertNotIn("sk-test", result["message"])

    def test_connection_model_not_found(self):
        exc = httpx.HTTPStatusError("404", request=_req(), response=httpx.Response(404, request=_req()))
        p, _ = _patch_client(exc)
        with p:
            result = _adapter().test_connection()
        self.assertEqual(result["error_code"], "MODEL_NOT_FOUND")

    def test_connection_malformed_response(self):
        resp = httpx.Response(200, request=_req(), json={"foo": "bar"})
        p, _ = _patch_client(resp)
        with p:
            result = _adapter().test_connection()
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "PROVIDER_ERROR")


if __name__ == "__main__":
    unittest.main()
