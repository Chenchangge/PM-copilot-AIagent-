"""P1-2 用户中心：学习记录 / 面试记录真实数据与分页。"""
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/profile.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.interview import InterviewEvaluation, InterviewSession  # noqa: E402
from app.models.learning import KnowledgeLearningRecord  # noqa: E402

HEADERS = {"X-User-Id": "history-user"}


class TestProfileHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        db = SessionLocal()
        try:
            db.add_all(
                [
                    KnowledgeLearningRecord(
                        user_id="history-user",
                        knowledge_point_id="mvp",
                        status="completed",
                        actual_minutes=20,
                    ),
                    KnowledgeLearningRecord(
                        user_id="history-user",
                        knowledge_point_id="rag-basics",
                        status="started",
                    ),
                    KnowledgeLearningRecord(
                        user_id="history-user",
                        knowledge_point_id="agent-basics",
                        status="completed",
                    ),
                    KnowledgeLearningRecord(
                        user_id="other-user",
                        knowledge_point_id="mvp",
                        status="completed",
                    ),
                ]
            )
            db.add_all(
                [
                    InterviewSession(
                        id="intv-completed",
                        user_id="history-user",
                        direction="AI产品经理",
                        difficulty="中等",
                        interview_type="AI产品",
                        status="completed",
                        config_snapshot={},
                        current_round=5,
                    ),
                    InterviewSession(
                        id="intv-unfinished",
                        user_id="history-user",
                        direction="C端产品经理",
                        difficulty="基础",
                        interview_type="产品基础",
                        status="waiting_answer",
                        config_snapshot={},
                        current_round=1,
                    ),
                    InterviewSession(
                        id="intv-completed-noeval",
                        user_id="history-user",
                        direction="数据产品经理",
                        difficulty="困难",
                        interview_type="数据分析",
                        status="completed",
                        config_snapshot={},
                        current_round=5,
                    ),
                    InterviewSession(
                        id="intv-other",
                        user_id="other-user",
                        direction="AI产品经理",
                        difficulty="中等",
                        interview_type="AI产品",
                        status="completed",
                        config_snapshot={},
                        current_round=5,
                    ),
                ]
            )
            db.add(
                InterviewEvaluation(
                    session_id="intv-completed",
                    user_id="history-user",
                    status="completed",
                    overall_score=81,
                    dimensions=[],
                    overall_strengths=[],
                    overall_weaknesses=[],
                    recommended_knowledge=[],
                )
            )
            db.commit()
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def test_learning_history_real_data(self):
        data = self.client.get("/api/profile/learning-history", headers=HEADERS).json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)
        first = data["items"][0]
        self.assertEqual(first["knowledge_point_id"], "agent-basics")
        self.assertTrue(first["title"])
        self.assertTrue(first["category"])
        self.assertGreater(first["duration_minutes"], 0)
        self.assertTrue(any(i["status"] == "started" for i in data["items"]))

    def test_learning_history_pagination(self):
        data = self.client.get(
            "/api/profile/learning-history", params={"page": 1, "page_size": 1}, headers=HEADERS
        ).json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 1)

    def test_interview_history_scores_and_actions(self):
        data = self.client.get("/api/profile/interview-history", headers=HEADERS).json()
        self.assertEqual(data["total"], 3)
        by_id = {i["session_id"]: i for i in data["items"]}
        self.assertEqual(by_id["intv-completed"]["overall_score"], 81)
        self.assertTrue(by_id["intv-completed"]["can_view_evaluation"])
        self.assertFalse(by_id["intv-completed"]["can_continue"])
        self.assertTrue(by_id["intv-unfinished"]["can_continue"])
        self.assertIsNone(by_id["intv-unfinished"]["overall_score"])
        self.assertTrue(by_id["intv-completed-noeval"]["can_view_evaluation"])
        self.assertIsNone(by_id["intv-completed-noeval"]["overall_score"])

    def test_user_isolation(self):
        data = self.client.get(
            "/api/profile/interview-history", headers={"X-User-Id": "other-user"}
        ).json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["session_id"], "intv-other")


if __name__ == "__main__":
    unittest.main()
