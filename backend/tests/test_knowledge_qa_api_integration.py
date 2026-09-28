"""知识问答 API 真实链路联调测试（不 Mock Pipeline，走真实 ModelService / DB / 错误处理器）。

无真实 Embedding / LLM Key 时，验证「配置缺失 → 友好错误」与「错误不泄漏」的真实契约；
成功回答与空检索在 test_knowledge_qa_api.py（Mock Pipeline）中覆盖。
"""
import os
import tempfile
import unittest

# 必须在导入 app 之前指定测试数据库，避免污染真实 pm_copilot.db
_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


def _post(client, user_id, json):
    return client.post("/api/knowledge/qa", json=json, headers={"X-User-Id": user_id})


class TestKnowledgeQaRealAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def test_no_models_returns_embedding_model_not_found(self):
        # 未配置任何模型 → build_rag_pipeline 先缺 Embedding 模型
        resp = _post(self.client, "user-no-models", {"query": "什么是 MVP？"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "EMBEDDING_MODEL_NOT_FOUND")

    def test_embedding_only_returns_llm_model_not_found(self):
        # 仅配置 Embedding 模型（无 text_generation）→ 缺文本生成模型
        headers = {"X-User-Id": "user-embedding-only"}
        self.client.post(
            "/api/models",
            json={"name": "Embedding", "provider": "openai", "model": "text-embedding-3-small", "api_key": "sk-test-embed"},
            headers=headers,
        )
        resp = _post(self.client, "user-embedding-only", {"query": "什么是 MVP？"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "LLM_MODEL_NOT_FOUND")

    def test_invalid_query_returns_400(self):
        resp = _post(self.client, "user-invalid-query", {"query": "   "})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "RETRIEVAL_INVALID_QUERY")

    def test_error_response_has_no_traceback_or_key(self):
        resp = _post(self.client, "user-clean-error", {"query": "什么是 MVP？"})
        text = resp.text.lower()
        self.assertNotIn("traceback", text)
        self.assertNotIn("sk-", text)
        self.assertNotIn("api_key", text)
        self.assertNotIn("file \"", text)


if __name__ == "__main__":
    unittest.main()
