"""知识库 AI 问答 API 测试（Mock RAGPipeline，不依赖真实 Chroma / Embedding / LLM）。

覆盖：Request 校验 / User ID / Pipeline 调用与传参 / 空检索 / 错误映射 / 安全 / Route 边界。
"""
import inspect
import os
import tempfile
import unittest
from unittest.mock import patch

# 必须在导入 app 之前指定测试数据库，避免污染真实 pm_copilot.db
_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.errors import AIErrorCode  # noqa: E402
from app.db.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.rag.errors import RAGError, RAGErrorCode  # noqa: E402
from app.rag.schemas import RAGResult, Source  # noqa: E402

import app.api.routes.knowledge_qa as kqa  # noqa: E402

HEADERS = {"X-User-Id": "test-user-1"}
NO_CONTEXT_ANSWER = "当前知识库中没有找到足够相关的信息，暂时无法基于知识库回答该问题。"


def _make_result(**overrides) -> RAGResult:
    kwargs = {
        "query": "什么是 MVP？",
        "answer": "MVP 是最小可行产品。",
        "sources": [
            Source(
                knowledge_id="mvp",
                chunk_id="mvp:0:0",
                title="MVP",
                category="product",
                section="定义",
                source_path="knowledge/data/product/mvp.md",
                score=0.9,
            )
        ],
        "retrieval_count": 1,
        "provider": "deepseek",
        "model": "deepseek-flash",
        "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
    }
    kwargs.update(overrides)
    return RAGResult(**kwargs)


class MockPipeline:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def run(self, query, top_k=5, similarity_threshold=None, max_distance=None):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
                "max_distance": max_distance,
            }
        )
        if self.error:
            raise self.error
        return self.result


def _post(client, json, headers=HEADERS):
    return client.post("/api/knowledge/qa", json=json, headers=headers)


def _post_raw(client, body: str, headers=HEADERS):
    """发送原始 JSON 文本（用于测试 NaN / Infinity 等非标准 JSON 扩展）。"""
    return client.post(
        "/api/knowledge/qa",
        content=body.encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
    )


def _patch_pipeline(pipeline):
    return patch("app.api.routes.knowledge_qa.build_rag_pipeline", return_value=pipeline)


class TestKnowledgeQAAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    # ---- 正常请求 / 序列化 ----
    def test_normal_request(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "什么是 MVP？"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["query"], "什么是 MVP？")
        self.assertEqual(data["answer"], "MVP 是最小可行产品。")
        self.assertEqual(data["retrieval_count"], 1)
        self.assertEqual(data["sources"][0]["knowledge_id"], "mvp")
        self.assertEqual(data["sources"][0]["source_path"], "knowledge/data/product/mvp.md")
        self.assertEqual(data["sources"][0]["score"], 0.9)
        self.assertEqual(data["provider"], "deepseek")
        self.assertEqual(data["model"], "deepseek-flash")
        self.assertEqual(data["usage"]["total_tokens"], 30)

    def test_empty_retrieval_http_200(self):
        result = _make_result(answer=NO_CONTEXT_ANSWER, sources=[], retrieval_count=0, usage=None)
        with _patch_pipeline(MockPipeline(result=result)):
            resp = _post(self.client, {"query": "什么是 RAG"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["answer"], NO_CONTEXT_ANSWER)
        self.assertEqual(data["sources"], [])
        self.assertEqual(data["retrieval_count"], 0)

    # ---- Request 校验 ----
    def test_query_missing(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {})
        self.assertEqual(resp.status_code, 422)  # Pydantic 必填字段缺失

    def test_query_empty(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": ""})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_QUERY")

    def test_query_whitespace_only(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "   "})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_QUERY")

    def test_query_too_long(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "长" * 2001})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_QUERY")

    def test_top_k_default(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pipeline.calls[0]["top_k"], 5)

    def test_top_k_1(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            resp = _post(self.client, {"query": "q", "top_k": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pipeline.calls[0]["top_k"], 1)

    def test_top_k_20(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            resp = _post(self.client, {"query": "q", "top_k": 20})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pipeline.calls[0]["top_k"], 20)

    def test_top_k_0(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q", "top_k": 0})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_TOP_K")

    def test_top_k_21(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q", "top_k": 21})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_TOP_K")

    def test_similarity_threshold_valid(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            resp = _post(self.client, {"query": "q", "similarity_threshold": 0.5})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pipeline.calls[0]["similarity_threshold"], 0.5)

    def test_similarity_threshold_out_of_range(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q", "similarity_threshold": 1.5})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_THRESHOLD")

    def test_similarity_threshold_nan(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post_raw(self.client, '{"query": "q", "similarity_threshold": NaN}')
        self.assertEqual(resp.status_code, 400)

    def test_max_distance_valid(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            resp = _post(self.client, {"query": "q", "max_distance": 0.3})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pipeline.calls[0]["max_distance"], 0.3)

    def test_max_distance_out_of_range(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q", "max_distance": 2.5})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_THRESHOLD")

    def test_max_distance_inf(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post_raw(self.client, '{"query": "q", "max_distance": Infinity}')
        self.assertEqual(resp.status_code, 400)

    def test_both_thresholds_conflict(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q", "similarity_threshold": 0.5, "max_distance": 0.5})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_THRESHOLD_CONFLICT")

    # ---- User ID ----
    def test_user_id_header_passed(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline) as m:
            resp = _post(self.client, {"query": "q"}, headers={"X-User-Id": "user-a"})
        self.assertEqual(resp.status_code, 200)
        m.assert_called_once_with("user-a")

    def test_user_id_default_anonymous(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline) as m:
            resp = _post(self.client, {"query": "q"}, headers={})
        self.assertEqual(resp.status_code, 200)
        m.assert_called_once_with("anonymous")

    # ---- Pipeline 调用 / 传参 ----
    def test_pipeline_receives_trimmed_query(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            _post(self.client, {"query": "  什么是 MVP？  "})
        self.assertEqual(pipeline.calls[0]["query"], "什么是 MVP？")

    def test_pipeline_receives_all_params(self):
        pipeline = MockPipeline(result=_make_result())
        with _patch_pipeline(pipeline):
            _post(self.client, {"query": "q", "top_k": 3, "similarity_threshold": 0.6})
        call = pipeline.calls[0]
        self.assertEqual(call["top_k"], 3)
        self.assertEqual(call["similarity_threshold"], 0.6)
        self.assertIsNone(call["max_distance"])

    # ---- 错误映射 ----
    def test_llm_model_not_found(self):
        err = RAGError(RAGErrorCode.llm_model_not_found, "未找到支持文本生成的模型。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "LLM_MODEL_NOT_FOUND")

    def test_index_not_found(self):
        err = RAGError(RAGErrorCode.index_not_found, "知识库索引不存在，请先构建索引。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "INDEX_NOT_FOUND")

    def test_index_model_mismatch(self):
        err = RAGError(RAGErrorCode.index_model_mismatch, "Embedding 模型不一致。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 409)

    def test_invalid_api_key(self):
        err = RAGError(AIErrorCode.invalid_api_key, "API Key 无效，请检查配置。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_API_KEY")

    def test_rate_limited(self):
        err = RAGError(AIErrorCode.rate_limited, "请求过于频繁，请稍后重试。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 429)

    def test_timeout(self):
        err = RAGError(AIErrorCode.timeout, "连接超时，请稍后重试。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 504)

    def test_provider_error(self):
        err = RAGError(AIErrorCode.provider_error, "模型服务返回错误，请稍后重试。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 502)

    def test_unknown(self):
        err = RAGError(AIErrorCode.unknown, "连接失败，请检查配置后重试。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 500)

    # ---- 安全 ----
    def test_response_does_not_contain_api_key(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q"})
        self.assertNotIn("sk-", resp.text)
        self.assertNotIn("api_key", resp.text.lower())
        self.assertNotIn("authorization", resp.text.lower())

    def test_error_response_is_clean(self):
        err = RAGError(AIErrorCode.invalid_api_key, "API Key 无效，请检查配置。")
        with _patch_pipeline(MockPipeline(error=err)):
            resp = _post(self.client, {"query": "q"})
        self.assertEqual(resp.status_code, 502)
        body = resp.json()
        self.assertEqual(body["error"]["code"], "INVALID_API_KEY")
        self.assertNotIn("sk-", resp.text)
        self.assertNotIn("traceback", resp.text.lower())
        self.assertNotIn("Traceback", resp.text)
        self.assertNotIn('File "', resp.text)

    def test_source_path_is_relative(self):
        with _patch_pipeline(MockPipeline(result=_make_result())):
            resp = _post(self.client, {"query": "q"})
        source_path = resp.json()["sources"][0]["source_path"]
        self.assertTrue(source_path.startswith("knowledge/data/"))
        self.assertNotIn("C:", source_path)
        self.assertNotIn("D:", source_path)
        self.assertNotIn("/home", source_path)
        self.assertNotIn("/Users", source_path)

    # ---- Route 边界（保持薄层）----
    def test_route_stays_thin(self):
        src = inspect.getsource(kqa)
        self.assertIn("pipeline.run(", src)
        self.assertNotIn("chromadb", src)
        self.assertNotIn("get_adapter", src)
        self.assertNotIn("OpenAICompatibleAdapter", src)
        self.assertNotIn("Retriever(", src)
        self.assertNotIn("build_messages(", src)


if __name__ == "__main__":
    unittest.main()
