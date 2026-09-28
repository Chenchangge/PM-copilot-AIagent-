"""AI 模型配置 API 测试（匿名 user_id + 内存 SQLite + mock 连通性）。"""
import os
import tempfile
import unittest
from unittest.mock import patch

# 必须在导入 app 之前指定测试数据库，避免污染真实 pm_copilot.db
_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402

HEADERS = {"X-User-Id": "test-user-1"}
FULL_KEY = "sk-test-1234abcd"


class TestModelsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def _create_model(self, **overrides):
        payload = {
            "name": "DeepSeek",
            "provider": "deepseek",
            "model": "deepseek-flash",
            "api_key": FULL_KEY,
        }
        payload.update(overrides)
        return self.client.post("/api/models", json=payload, headers=HEADERS)

    def test_create_and_get(self):
        resp = self._create_model()
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertNotIn(FULL_KEY, resp.text)  # 完整 Key 不出现在响应
        self.assertTrue(data["has_api_key"])
        self.assertTrue(data["masked_api_key"].endswith("abcd"))
        self.assertEqual(data["capabilities"]["text_generation"], "supported")

    def test_list_models_masks_key(self):
        self._create_model()
        resp = self.client.get("/api/models", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()), 1)
        self.assertNotIn(FULL_KEY, resp.text)

    def test_get_by_id_and_user_isolation(self):
        created = self._create_model().json()
        resp = self.client.get(f"/api/models/{created['id']}", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(FULL_KEY, resp.text)
        # 其他匿名用户不可见
        other = self.client.get(f"/api/models/{created['id']}", headers={"X-User-Id": "other-user"})
        self.assertEqual(other.status_code, 404)

    def test_update_model(self):
        created = self._create_model().json()
        resp = self.client.put(
            f"/api/models/{created['id']}",
            json={"name": "DeepSeek V3"},
            headers=HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "DeepSeek V3")
        self.assertNotIn(FULL_KEY, resp.text)

    def test_delete_model(self):
        created = self._create_model().json()
        resp = self.client.delete(f"/api/models/{created['id']}", headers=HEADERS)
        self.assertEqual(resp.status_code, 204)
        gone = self.client.get(f"/api/models/{created['id']}", headers=HEADERS)
        self.assertEqual(gone.status_code, 404)

    def test_resolve_by_capabilities(self):
        self._create_model()  # deepseek: reasoning / structured_output 均 supported
        resp = self.client.post(
            "/api/models/resolve",
            json={"required_capabilities": ["reasoning", "structured_output"]},
            headers=HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.json()["models"]), 1)

    def test_resolve_embedding_no_match(self):
        self._create_model()  # deepseek: embedding = unknown，不满足 supported
        resp = self.client.post(
            "/api/models/resolve",
            json={"required_capabilities": ["embedding"]},
            headers=HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["models"], [])
        self.assertIsNotNone(resp.json()["message"])

    def test_create_custom_embedding_model(self):
        # bge-m3 名字不含 "embedding"，靠 model_type=embedding 显式声明
        # 使用独立 user_id，避免影响其他测试对 test-user-1 的能力断言
        resp = self.client.post(
            "/api/models",
            json={"name": "Emb", "provider": "custom", "model": "bge-m3", "api_key": FULL_KEY, "model_type": "embedding"},
            headers={"X-User-Id": "custom-user"},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["capabilities"]["embedding"], "supported")
        self.assertNotIn(FULL_KEY, resp.text)

    def test_create_custom_model_type_invalid_rejected(self):
        resp = self.client.post(
            "/api/models",
            json={"name": "Emb", "provider": "custom", "model": "bge-m3", "api_key": FULL_KEY, "model_type": "invalid"},
            headers={"X-User-Id": "custom-user"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_test_connection_provider_not_supported(self):
        created = self._create_model(provider="gemini", model="gemini-pro").json()
        resp = self.client.post(f"/api/models/{created['id']}/test", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error_code"], "PROVIDER_ERROR")

    def test_test_connection_error_mapping(self):
        created = self._create_model().json()

        class FakeAdapter:
            def test_connection(self):
                return {
                    "success": False,
                    "model": "deepseek-flash",
                    "latency_ms": None,
                    "error_code": "INVALID_API_KEY",
                    "message": "API Key 无效，请检查配置。",
                }

        with patch("app.services.model_service.get_adapter", return_value=FakeAdapter()):
            resp = self.client.post(f"/api/models/{created['id']}/test", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["success"])
        self.assertEqual(resp.json()["error_code"], "INVALID_API_KEY")

    def test_update_keeps_key_when_omitted(self):
        created = self._create_model(api_key="old-secret-1234").json()
        resp = self.client.put(f"/api/models/{created['id']}", json={"name": "改名"}, headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["has_api_key"])
        self.assertTrue(body["masked_api_key"].endswith("1234"))  # 旧 Key 未被清除

    def test_update_replaces_key(self):
        created = self._create_model(api_key="old-secret-1234").json()
        resp = self.client.put(
            f"/api/models/{created['id']}",
            json={"api_key": "new-secret-9999"},
            headers=HEADERS,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["masked_api_key"].endswith("9999"))

    def test_user_isolation_put(self):
        created = self._create_model().json()
        resp = self.client.put(
            f"/api/models/{created['id']}",
            json={"name": "越权"},
            headers={"X-User-Id": "other-user"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_user_isolation_delete(self):
        created = self._create_model().json()
        resp = self.client.delete(f"/api/models/{created['id']}", headers={"X-User-Id": "other-user"})
        self.assertEqual(resp.status_code, 404)

    def test_user_isolation_test(self):
        created = self._create_model().json()
        resp = self.client.post(f"/api/models/{created['id']}/test", headers={"X-User-Id": "other-user"})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
