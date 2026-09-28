"""知识库 Learning API 测试（TestClient，不依赖 DB / 真实模型）。"""
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class TestKnowledgeAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_list(self):
        resp = self.client.get("/api/knowledge")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["total"], 200)
        ids = [i["id"] for i in data["items"]]
        self.assertIn("rag-basics", ids)

    def test_list_category(self):
        resp = self.client.get("/api/knowledge", params={"category": "ai-product"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["total"], 0)
        self.assertTrue(all(i["category"] == "ai-product" for i in data["items"]))

    def test_detail_rag(self):
        resp = self.client.get("/api/knowledge/rag-basics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], "rag-basics")
        self.assertTrue(data["definition"])
        self.assertTrue(data["core_content"])
        self.assertIsInstance(data["common_scenarios"], list)
        self.assertIsInstance(data["pm_focus"], list)

    def test_detail_not_found(self):
        resp = self.client.get("/api/knowledge/not-exist")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "KNOWLEDGE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
