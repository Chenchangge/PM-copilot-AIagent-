"""模拟面试 API 测试（TestClient + Mock 追问决策，不依赖真实模型）。"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402

HEADERS = {"X-User-Id": "api-user-1"}
CONFIG = {"direction": "AI产品经理", "difficulty": "中等", "interview_type": "AI产品"}


class MockLLM:
    def __init__(self, outputs=None, error=None):
        self.outputs = list(outputs or [])
        self.error = error
        self.provider = "mock"
        self.model = "mock-llm"

    def generate(self, messages, options=None):
        if self.error:
            raise self.error
        if self.outputs:
            return {"content": self.outputs.pop(0)}
        return {"content": json.dumps({"should_follow_up": False, "follow_up_type": None, "follow_up_question": None, "reason": "ok"})}

    def classify_error(self, exc):
        return "PROVIDER_ERROR", "模型服务返回错误"


class TestInterviewAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def _create(self, headers=HEADERS):
        return self.client.post("/api/interview/sessions", json=CONFIG, headers=headers)

    def test_create_session(self):
        resp = self._create()
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["status"], "waiting_answer")
        self.assertEqual(data["current_round"], 1)
        self.assertEqual(data["question"]["type"], "main")

    def test_create_invalid_config(self):
        resp = self.client.post("/api/interview/sessions", json={"direction": "X", "difficulty": "中等", "interview_type": "AI产品"}, headers=HEADERS)
        self.assertEqual(resp.status_code, 422)

    def test_get_session(self):
        sid = self._create().json()["session_id"]
        resp = self.client.get(f"/api/interview/sessions/{sid}", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["session"]["status"], "waiting_answer")
        self.assertGreaterEqual(len(data["turns"]), 1)

    def test_get_session_not_found(self):
        resp = self.client.get("/api/interview/sessions/nope", headers=HEADERS)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_SESSION_NOT_FOUND")

    def test_user_isolation(self):
        sid = self._create(headers={"X-User-Id": "user-a"}).json()["session_id"]
        resp = self.client.get(f"/api/interview/sessions/{sid}", headers={"X-User-Id": "user-b"})
        self.assertEqual(resp.status_code, 404)

    def test_submit_answer_followup(self):
        sid = self._create().json()["session_id"]
        with patch(
            "app.services.interview_service.resolve_interview_adapter",
            return_value=MockLLM(outputs=[json.dumps({"should_follow_up": True, "follow_up_type": "why", "follow_up_question": "追问", "reason": "x"})]),
        ):
            resp = self.client.post(f"/api/interview/sessions/{sid}/answer", json={"answer": "回答"}, headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["action"], "follow_up")

    def test_submit_answer_next_question(self):
        sid = self._create().json()["session_id"]
        with patch("app.services.interview_service.resolve_interview_adapter", return_value=MockLLM()):
            resp = self.client.post(f"/api/interview/sessions/{sid}/answer", json={"answer": "回答"}, headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["action"], "next_question")

    def test_submit_answer_model_not_found(self):
        # 不 patch 解析函数，空库无满足能力的模型
        sid = self._create().json()["session_id"]
        resp = self.client.post(f"/api/interview/sessions/{sid}/answer", json={"answer": "回答"}, headers=HEADERS)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_MODEL_NOT_FOUND")

    def test_empty_answer(self):
        sid = self._create().json()["session_id"]
        resp = self.client.post(f"/api/interview/sessions/{sid}/answer", json={"answer": "   "}, headers=HEADERS)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_INVALID_ANSWER")

    def test_answer_after_completed(self):
        sid = self._create().json()["session_id"]
        self.client.post(f"/api/interview/sessions/{sid}/finish", headers=HEADERS)
        resp = self.client.post(f"/api/interview/sessions/{sid}/answer", json={"answer": "回答"}, headers=HEADERS)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_SESSION_COMPLETED")

    def test_finish(self):
        sid = self._create().json()["session_id"]
        resp = self.client.post(f"/api/interview/sessions/{sid}/finish", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "completed")
        self.assertEqual(resp.json()["end_reason"], "manual")

    def test_finish_idempotent(self):
        sid = self._create().json()["session_id"]
        self.client.post(f"/api/interview/sessions/{sid}/finish", headers=HEADERS)
        resp = self.client.post(f"/api/interview/sessions/{sid}/finish", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "completed")


if __name__ == "__main__":
    unittest.main()
