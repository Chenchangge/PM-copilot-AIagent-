"""P1-3 计划可维护性：跳过 / 补卡 / 核心速成 / 进度不回退。"""
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/maint.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.learning import LearningPlanDay  # noqa: E402


class TestLearningMaintenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def _headers(self, uid):
        return {"X-User-Id": uid}

    def _create(self, uid, **overrides):
        body = {
            "target_type": "category",
            "target_id": "interview-job",
            "current_level": "基础",
            "daily_minutes": 30,
            "intensity": "标准",
            "selected_days": 16,
        }
        body.update(overrides)
        return self.client.post("/api/learning/plans", json=body, headers=self._headers(uid))

    def test_skip_task_reduces_denominator_without_progress_regression(self):
        plan = self._create("skip-user").json()
        tasks = [t for d in plan["days"] for t in d["tasks"]]
        self.assertGreaterEqual(len(tasks), 3)
        self.client.post(f"/api/learning/tasks/{tasks[0]['id']}/complete", headers=self._headers("skip-user"))
        before = self.client.get(f"/api/learning/plans/{plan['id']}", headers=self._headers("skip-user")).json()
        skipped = self.client.post(
            f"/api/learning/tasks/{tasks[1]['id']}/skip", headers=self._headers("skip-user")
        )
        self.assertEqual(skipped.status_code, 200)
        after = skipped.json()
        self.assertGreaterEqual(after["progress_percent"], before["progress_percent"])
        self.assertEqual(after["total_knowledge_points"], before["total_knowledge_points"] - 1)
        flat = {t["id"]: t for d in after["days"] for t in d["tasks"]}
        self.assertEqual(flat[tasks[1]["id"]]["status"], "skipped")
        # 整日跳过后，当前天应继续向后走，而不是停在已跳过的 Day
        self.assertEqual(after["current_day_number"], 3)
        # 跳过幂等
        again = self.client.post(
            f"/api/learning/tasks/{tasks[1]['id']}/skip", headers=self._headers("skip-user")
        )
        self.assertEqual(again.status_code, 200)
        # 已完成/已跳过的任务不能再 start/complete
        self.assertEqual(
            self.client.post(
                f"/api/learning/tasks/{tasks[1]['id']}/complete", headers=self._headers("skip-user")
            ).status_code,
            409,
        )

    def test_makeup_moves_yesterday_unfinished_to_today(self):
        plan = self._create("makeup-user", selected_days=6, target_id="interview-job").json()
        days = plan["days"]
        day1 = days[0]
        day2 = days[1]
        self.assertGreater(len(day1["tasks"]), 0)
        # 模拟「昨天已结束」：把 Day1 标成 completed，但保留 pending 任务，current_day 变 2
        db = SessionLocal()
        try:
            row = db.get(LearningPlanDay, day1["id"])
            row.status = "completed"
            db.commit()
        finally:
            db.close()

        resp = self.client.post(
            f"/api/learning/plans/{plan['id']}/makeup", headers=self._headers("makeup-user")
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["moved"], 0)
        day1_after = next(d for d in data["plan"]["days"] if d["id"] == day1["id"])
        day2_after = next(d for d in data["plan"]["days"] if d["id"] == day2["id"])
        moved_ids = {t["id"] for t in day1["tasks"] if t["status"] in ("pending", "in_progress")}
        self.assertEqual(day1_after["tasks"], [])
        self.assertTrue(moved_ids <= {t["id"] for t in day2_after["tasks"]})

    def test_selected_days_are_trimmed_to_avoid_empty_days(self):
        plan = self._create("trim-user", selected_days=30).json()
        self.assertEqual(plan["selected_days"], plan["total_knowledge_points"])
        self.assertTrue(all(d["tasks"] for d in plan["days"]))

    def test_crash_mode_is_capped_to_14_days(self):
        estimate = self.client.post(
            "/api/learning/plans/estimate",
            json={
                "target_type": "direction",
                "target_id": "AI产品经理",
                "current_level": "基础",
                "daily_minutes": 30,
                "intensity": "标准",
                "mode": "crash",
            },
            headers=self._headers("crash-user"),
        )
        self.assertEqual(estimate.status_code, 200)
        data = estimate.json()
        self.assertEqual(data["mode"], "crash")
        self.assertGreater(data["knowledge_count"], 0)
        self.assertLessEqual(data["recommended_days"], 14)

        plan = self.client.post(
            "/api/learning/plans",
            json={
                "target_type": "direction",
                "target_id": "AI产品经理",
                "current_level": "基础",
                "daily_minutes": 30,
                "intensity": "标准",
                "mode": "crash",
                "selected_days": data["recommended_days"],
            },
            headers=self._headers("crash-user"),
        )
        self.assertEqual(plan.status_code, 201)
        self.assertLessEqual(plan.json()["selected_days"], 14)
        self.assertLessEqual(len(plan.json()["days"]), 14)


if __name__ == "__main__":
    unittest.main()
