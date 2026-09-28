"""Learning Plan / Taxonomy 测试（Step 12-3 §41 / §42）。"""
import math
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/learning_test.db"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.learning.constants import QUALITY_DEPRECATED, QUALITY_DRAFT  # noqa: E402
from app.learning.dependency import has_cycle, order_points  # noqa: E402
from app.learning.errors import LearningError  # noqa: E402
from app.learning.knowledge_index import (  # noqa: E402
    KnowledgePointView,
    build_knowledge_index,
    fallback_minutes,
    resolve_target,
)
from app.learning.planner import (  # noqa: E402
    compute_recommended_days,
    compute_total_minutes,
    filter_recommendable,
)
from app.learning.service import LearningService  # noqa: E402
from app.main import app  # noqa: E402


def _pt(id_, category="ai", difficulty="入门", minutes=10, quality="reviewed", deps=None, tags=None, topic=None):
    return KnowledgePointView(
        id=id_,
        title=id_,
        category=category,
        topic=topic or category,
        tags=tags or [],
        difficulty=difficulty,
        estimated_minutes=minutes,
        quality_status=quality,
        dependencies=deps or [],
    )


# ================= 单元测试：排课 / 依赖 / 回退 =================
class TestPlanner(unittest.TestCase):
    def test_filter_recommendable_excludes_draft_deprecated(self):
        pts = [
            _pt("a", quality="reviewed"),
            _pt("b", quality="verified"),
            _pt("c", quality=QUALITY_DRAFT),
            _pt("d", quality=QUALITY_DEPRECATED),
        ]
        out = filter_recommendable(pts)
        self.assertEqual({p.id for p in out}, {"a", "b"})

    def test_total_minutes(self):
        pts = [_pt("a", minutes=10), _pt("b", minutes=20), _pt("c", minutes=30)]
        self.assertEqual(compute_total_minutes(pts), 60)

    def test_recommended_days(self):
        self.assertEqual(compute_recommended_days(210, 30), 7)
        self.assertEqual(compute_recommended_days(0, 30), 1)
        self.assertEqual(compute_recommended_days(31, 30), 2)

    def test_fallback_minutes_snaps_to_allowed(self):
        self.assertEqual(fallback_minutes("入门", 100), 10)
        self.assertEqual(fallback_minutes("进阶", 100), 20)
        # 长正文追加后收敛到允许值
        self.assertEqual(fallback_minutes("入门", 5000), 20)

    def test_resolve_target_category_topic_tag(self):
        index = {
            "a": _pt("a", category="ai", tags=["RAG"]),
            "b": _pt("b", category="ai", tags=["Embedding"]),
            "c": _pt("c", category="data", tags=["SQL"]),
        }
        self.assertEqual({p.id for p in resolve_target(index, "category", "ai")}, {"a", "b"})
        self.assertEqual({p.id for p in resolve_target(index, "topic", "ai")}, {"a", "b"})
        self.assertEqual({p.id for p in resolve_target(index, "tag", "RAG")}, {"a"})


class TestDependency(unittest.TestCase):
    def test_topological_sort_chain(self):
        pts = [_pt("A", deps=["B"]), _pt("B"), _pt("C", deps=["A"])]
        ordered = [p.id for p in order_points(pts)]
        self.assertLess(ordered.index("B"), ordered.index("A"))
        self.assertLess(ordered.index("A"), ordered.index("C"))

    def test_cycle_rejected(self):
        pts = [_pt("A", deps=["B"]), _pt("B", deps=["A"])]
        self.assertTrue(has_cycle(pts))
        with self.assertRaises(LearningError):
            order_points(pts)

    def test_chain_no_cycle(self):
        pts = [_pt("A", deps=["B"]), _pt("B", deps=["C"]), _pt("C")]
        self.assertFalse(has_cycle(pts))


# ================= 单元测试：AI 解释（非单点故障） =================
class _MockLLM:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error

    def generate(self, messages, options=None):
        if self.error:
            raise self.error
        return {"content": self.content}


class TestAIExplain(unittest.TestCase):
    def setUp(self):
        # 空库：无模型配置，走 fallback
        init_db()
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_ai_explain_unavailable_falls_back(self):
        svc = LearningService(self.db, llm_adapter=None, knowledge_index={})
        ctx = {"target_name": "AI产品", "knowledge_count": 10, "total_minutes": 210,
               "daily_minutes": 30, "recommended_days": 7, "key_topics": ["RAG"]}
        text = svc._ai_explain("no-model-user", ctx)
        self.assertIn("210", text)

    def test_ai_explain_normal_response(self):
        svc = LearningService(self.db, llm_adapter=_MockLLM(content="建议 7-9 天完成"), knowledge_index={})
        ctx = {"target_name": "AI产品", "knowledge_count": 10, "total_minutes": 210,
               "daily_minutes": 30, "recommended_days": 7, "key_topics": []}
        text = svc._ai_explain("u", ctx)
        self.assertEqual(text, "建议 7-9 天完成")

    def test_ai_explain_exception_falls_back(self):
        svc = LearningService(self.db, llm_adapter=_MockLLM(error=TimeoutError()), knowledge_index={})
        ctx = {"target_name": "AI产品", "knowledge_count": 10, "total_minutes": 210,
               "daily_minutes": 30, "recommended_days": 7, "key_topics": []}
        text = svc._ai_explain("u", ctx)
        self.assertIn("210", text)  # 回退确定性文案


# ================= 集成测试：API =================
class TestLearningAPI(unittest.TestCase):
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

    def _estimate(self, uid, **overrides):
        body = {
            "target_type": "category",
            "target_id": "ai-product",
            "current_level": "入门",
            "daily_minutes": 30,
            "intensity": "标准",
        }
        body.update(overrides)
        return self.client.post("/api/learning/plans/estimate", json=body, headers=self._headers(uid))

    def _create(self, uid, **overrides):
        body = {
            "target_type": "category",
            "target_id": "ai-product",
            "current_level": "入门",
            "daily_minutes": 30,
            "intensity": "标准",
            "selected_days": 7,
        }
        body.update(overrides)
        return self.client.post("/api/learning/plans", json=body, headers=self._headers(uid))

    # ---- estimate ----
    def test_estimate_category(self):
        resp = self._estimate("est-cat")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["knowledge_count"], 0)  # ai-product 分类 10 个知识点
        self.assertEqual(data["recommended_days"], compute_recommended_days(data["total_minutes"], 30))
        self.assertIn(data["recommended_days"], data["day_choices"])
        self.assertTrue(data["explanation"])

    def test_estimate_topic(self):
        resp = self._estimate("est-topic", target_type="topic", target_id="rag-retrieval")
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(resp.json()["knowledge_count"], 0)  # rag / embedding / vector-database

    def test_estimate_tag(self):
        resp = self._estimate("est-tag", target_type="tag", target_id="RAG")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["knowledge_count"], 1)

    def test_estimate_empty_target(self):
        resp = self._estimate("est-empty", target_id="nonexistent-category")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "LEARNING_TARGET_EMPTY")

    def test_estimate_invalid_level(self):
        resp = self._estimate("est-invalid", current_level="高手")
        self.assertEqual(resp.status_code, 422)

    # ---- create plan / days / tasks ----
    def test_create_plan(self):
        resp = self._create("plan-1")
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["status"], "active")
        self.assertGreater(data["total_knowledge_points"], 0)
        self.assertEqual(data["selected_days"], 7)
        self.assertEqual(len(data["days"]), 7)
        total_tasks = sum(len(d["tasks"]) for d in data["days"])
        self.assertGreater(total_tasks, 0)

    def test_plan_days_and_tasks_consistent(self):
        data = self._create("plan-2").json()
        for day in data["days"]:
            task_sum = sum(t["estimated_minutes"] for t in day["tasks"])
            self.assertEqual(day["planned_minutes"], task_sum)

    def test_complete_task_updates_day_and_plan(self):
        data = self._create("plan-3").json()
        first_day = next(d for d in data["days"] if d["tasks"])
        task_id = first_day["tasks"][0]["id"]
        resp = self.client.post(f"/api/learning/tasks/{task_id}/complete", headers=self._headers("plan-3"))
        self.assertEqual(resp.status_code, 200)
        out = resp.json()
        self.assertEqual(out["completed_knowledge_points"], 1)
        self.assertGreater(out["progress_percent"], 0)
        updated_day = next(d for d in out["days"] if d["id"] == first_day["id"])
        self.assertGreater(updated_day["completed_minutes"], 0)

    def test_start_task_sets_in_progress(self):
        data = self._create("plan-4").json()
        first_day = next(d for d in data["days"] if d["tasks"])
        task_id = first_day["tasks"][0]["id"]
        resp = self.client.post(f"/api/learning/tasks/{task_id}/start", headers=self._headers("plan-4"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "in_progress")

    # ---- pause / resume ----
    def test_pause_resume(self):
        data = self._create("plan-5").json()
        pid = data["id"]
        p = self.client.post(f"/api/learning/plans/{pid}/pause", headers=self._headers("plan-5"))
        self.assertEqual(p.json()["status"], "paused")
        r = self.client.post(f"/api/learning/plans/{pid}/resume", headers=self._headers("plan-5"))
        self.assertEqual(r.json()["status"], "active")

    # ---- 重新排期 ----
    def test_reschedule_preserves_completed(self):
        data = self._create("plan-6").json()
        pid = data["id"]
        tasks = [t for d in data["days"] for t in d["tasks"]]
        # 完成前 2 个任务
        for t in tasks[:2]:
            self.client.post(f"/api/learning/tasks/{t['id']}/complete", headers=self._headers("plan-6"))
        before = self.client.get(f"/api/learning/plans/{pid}", headers=self._headers("plan-6")).json()
        completed_before = {
            t["knowledge_point_id"]: next(d["day_number"] for d in before["days"] if t["id"] in {x["id"] for x in d["tasks"]})
            for d in before["days"] for t in d["tasks"] if t["status"] == "completed"
        }
        resp = self.client.patch(
            f"/api/learning/plans/{pid}",
            json={"selected_days": 4, "daily_minutes": 45},
            headers=self._headers("plan-6"),
        )
        self.assertEqual(resp.status_code, 200)
        after = resp.json()
        self.assertEqual(after["completed_knowledge_points"], 2)
        self.assertGreater(after["total_knowledge_points"], 0)
        # 已完成任务仍在其原 Day 且保持 completed
        for d in after["days"]:
            for t in d["tasks"]:
                if t["knowledge_point_id"] in completed_before:
                    self.assertEqual(t["status"], "completed")
                    self.assertEqual(d["day_number"], completed_before[t["knowledge_point_id"]])

    # ---- 学习记录 ----
    def test_knowledge_learning_record(self):
        resp = self.client.post("/api/learning/knowledge/rag-basics/start", headers=self._headers("rec-1"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "started")
        resp2 = self.client.post("/api/learning/knowledge/rag-basics/complete", headers=self._headers("rec-1"))
        self.assertEqual(resp2.json()["status"], "completed")

    def test_knowledge_record_unknown_knowledge(self):
        resp = self.client.post("/api/learning/knowledge/nope/start", headers=self._headers("rec-2"))
        self.assertEqual(resp.status_code, 404)

    # ---- 首页摘要 ----
    def test_home_summary(self):
        self._create("home-1")
        resp = self.client.get("/api/learning/home-summary", headers=self._headers("home-1"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNotNone(data["active_plan"])
        self.assertEqual(data["active_plan"]["target_name"], "AI产品")

    def test_home_summary_empty(self):
        resp = self.client.get("/api/learning/home-summary", headers=self._headers("home-none"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.json()["active_plan"])

    # ---- deprecated 不影响历史计划 ----
    def test_deprecated_knowledge_plan_compat(self):
        uid = "dep-1"
        data = self._create(uid).json()
        pid = data["id"]
        # 用「空索引」模拟知识点被下架/移除，读取计划不应崩溃
        db = SessionLocal()
        try:
            svc = LearningService(db, knowledge_index={})
            detail = svc.get_plan(uid, pid)
            self.assertGreater(detail.total_knowledge_points, 0)
            for d in detail.days:
                for t in d.tasks:
                    self.assertTrue(t.title)  # 回退为 knowledge_point_id
        finally:
            db.close()

    # ---- 面试推荐入口 ----
    def test_interview_recommendation_threshold(self):
        uid = "iv-1"
        data = self._create(uid).json()
        pid = data["id"]
        tasks = [t for d in data["days"] for t in d["tasks"]]
        # 完成 >=70% 后触发推荐（动态计算，避免硬编码任务数）
        n = math.ceil(len(tasks) * 0.7)
        for t in tasks[:n]:
            self.client.post(f"/api/learning/tasks/{t['id']}/complete", headers=self._headers(uid))
        detail = self.client.get(f"/api/learning/plans/{pid}", headers=self._headers(uid)).json()
        self.assertIsNotNone(detail["recommended_interview"])
        self.assertTrue(detail["recommended_interview"]["eligible"])

    def test_no_interview_recommendation_below_threshold(self):
        uid = "iv-2"
        data = self._create(uid).json()
        pid = data["id"]
        tasks = [t for d in data["days"] for t in d["tasks"]]
        self.client.post(f"/api/learning/tasks/{tasks[0]['id']}/complete", headers=self._headers(uid))
        detail = self.client.get(f"/api/learning/plans/{pid}", headers=self._headers(uid)).json()
        self.assertIsNone(detail["recommended_interview"])


if __name__ == "__main__":
    unittest.main()
