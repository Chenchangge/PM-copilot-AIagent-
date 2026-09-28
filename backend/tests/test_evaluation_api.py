"""面试评价 API 测试（TestClient + Mock LLM，不依赖真实模型）。"""
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

HEADERS = {"X-User-Id": "eval-user-1"}
CONFIG = {"direction": "AI产品经理", "difficulty": "中等", "interview_type": "AI产品"}

_DIMS = [
    {"dimension": "产品思维", "score": 84, "evidence": [], "strengths": ["s"], "weaknesses": ["w"]},
    {"dimension": "需求分析", "score": 76, "evidence": [], "strengths": ["s"], "weaknesses": ["w"]},
    {"dimension": "逻辑与表达", "score": 88, "evidence": [], "strengths": ["s"], "weaknesses": ["w"]},
    {"dimension": "AI知识", "score": 71, "evidence": [], "strengths": ["s"], "weaknesses": ["w"]},
    {"dimension": "业务意识", "score": 80, "evidence": [], "strengths": ["s"], "weaknesses": ["w"]},
]


def _valid_json():
    return json.dumps({
        "dimensions": _DIMS,
        "overall_strengths": ["s"],
        "overall_weaknesses": ["w"],
        "summary": "总结",
    })


class MockLLM:
    def __init__(self, outputs=None):
        self.outputs = list(outputs or [])
        self.provider = "mock"
        self.model = "mock-llm"
        self.calls = 0

    def generate(self, messages, options=None):
        self.calls += 1
        return {"content": self.outputs.pop(0)}

    def classify_error(self, exc):
        return "PROVIDER_ERROR", "模型服务返回错误"


class TestEvaluationAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def _create_completed(self):
        sid = self.client.post("/api/interview/sessions", json=CONFIG, headers=HEADERS).json()["session_id"]
        self.client.post(f"/api/interview/sessions/{sid}/finish", headers=HEADERS)
        return sid

    # ---- POST ----
    def test_session_not_found(self):
        resp = self.client.post("/api/interview/sessions/nope/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_SESSION_NOT_FOUND")

    def test_session_not_completed(self):
        sid = self.client.post("/api/interview/sessions", json=CONFIG, headers=HEADERS).json()["session_id"]
        resp = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_INVALID_STATE")

    def test_no_interview_model(self):
        sid = self._create_completed()
        # 不 patch 解析函数，空库无满足能力的模型
        resp = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "INTERVIEW_MODEL_NOT_FOUND")

    def test_successful_evaluation(self):
        sid = self._create_completed()
        with patch("app.services.evaluation_service.resolve_interview_adapter", return_value=MockLLM(outputs=[_valid_json()])):
            resp = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["overall_score"], 81)
        self.assertEqual(len(data["dimensions"]), 5)

    def test_repeated_post_no_duplicate_llm(self):
        sid = self._create_completed()
        llm = MockLLM(outputs=[_valid_json()])
        with patch("app.services.evaluation_service.resolve_interview_adapter", return_value=llm):
            first = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS).json()
            second = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS).json()
        self.assertEqual(first["evaluation_id"], second["evaluation_id"])
        self.assertEqual(llm.calls, 1)

    def test_invalid_output_retry_once(self):
        sid = self._create_completed()
        llm = MockLLM(outputs=["garbage", _valid_json()])
        with patch("app.services.evaluation_service.resolve_interview_adapter", return_value=llm):
            resp = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(llm.calls, 2)

    def test_retry_still_invalid_returns_failed(self):
        sid = self._create_completed()
        with patch("app.services.evaluation_service.resolve_interview_adapter", return_value=MockLLM(outputs=["garbage", "still garbage"])):
            resp = self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.json()["error"]["code"], "EVALUATION_FAILED")

    # ---- GET ----
    def test_get_not_found(self):
        sid = self._create_completed()
        resp = self.client.get(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "EVALUATION_NOT_FOUND")

    def test_get_completed(self):
        sid = self._create_completed()
        with patch("app.services.evaluation_service.resolve_interview_adapter", return_value=MockLLM(outputs=[_valid_json()])):
            self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        resp = self.client.get(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "completed")
        self.assertEqual(resp.json()["overall_score"], 81)

    def test_get_failed(self):
        sid = self._create_completed()
        with patch("app.services.evaluation_service.resolve_interview_adapter", return_value=MockLLM(outputs=["garbage", "garbage"])):
            self.client.post(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        resp = self.client.get(f"/api/interview/sessions/{sid}/evaluation", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "failed")
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
