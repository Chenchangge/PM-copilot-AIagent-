"""P0-1 学习计划目标选择重构：路径卡 / scope=plan / 难度与强度生效。

这些测试锁定 test1 验收表：
- 计划页不再收到 640 个标签；
- 三张路径卡的数字来自后端，且与 estimate / 创建出的计划一致；
- 当前水平改变知识点数量，学习强度改变天数；
- 计划排课不再出现「最后一天吸收全部任务」。
"""
import json
import unittest

from fastapi.testclient import TestClient

from app.db.database import Base, engine, init_db
from app.learning.knowledge_index import KnowledgePointView
from app.learning.planner import distribute
from app.main import app

PLAN_QUERY = "scope=plan&current_level=基础&daily_minutes=30&intensity=标准"


def _point(idx: int, minutes: int = 20) -> KnowledgePointView:
    return KnowledgePointView(
        id=f"p{idx}",
        title=f"知识点 {idx}",
        category="ai-product",
        topic="rag-retrieval",
        difficulty="进阶",
        estimated_minutes=minutes,
        quality_status="reviewed",
    )


class TestPlanTaxonomyShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def test_scope_plan_shape_and_no_full_tags(self):
        resp = self.client.get(f"/api/learning/taxonomy?{PLAN_QUERY}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(len(data["paths"]), 3)
        self.assertEqual(len(data["categories"]), 11)
        self.assertEqual(sum(1 for c in data["categories"] if c["featured"]), 5)
        self.assertEqual(len(data["directions"]), 4)
        self.assertEqual(len(data["daily_minutes"]), 4)
        self.assertNotIn("tags", data)  # 关键：不再下发 640 个标签
        self.assertLessEqual(len(data["recommended_tags"]), 3)

        # topics 必须是「按分类分组」的 dict，而不是 22 条扁平列表
        self.assertIsInstance(data["topics"], dict)
        self.assertEqual(len(data["topics"]), 11)
        for rows in data["topics"].values():
            self.assertIsInstance(rows, list)

        # 响应体必须足够小，避免又把数据库字段直接倒给前端
        self.assertLess(len(json.dumps(data, ensure_ascii=False)), 30000)

    def test_featured_categories_order(self):
        data = self.client.get(f"/api/learning/taxonomy?{PLAN_QUERY}").json()
        featured = [c["id"] for c in data["categories"] if c["featured"]]
        self.assertEqual(
            featured,
            ["product-foundation", "data-analysis", "ai-product", "user-research", "interview-job"],
        )

    def test_default_taxonomy_compat(self):
        data = self.client.get("/api/learning/taxonomy").json()
        self.assertEqual(len(data["categories"]), 11)
        self.assertEqual(len(data["topics"]), 22)
        self.assertEqual(len(data["tags"]), 640)  # 旧行为保留给知识库页
        self.assertIsInstance(data["topics"], list)


class TestPathCards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.cards = {
            p["id"]: p
            for p in cls.client.get(f"/api/learning/taxonomy?{PLAN_QUERY}").json()["paths"]
        }

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)

    def _estimate(self, path_id: str, user: str = "path-est"):
        return self.client.post(
            "/api/learning/plans/estimate",
            json={
                "path_id": path_id,
                "current_level": "基础",
                "daily_minutes": 30,
                "intensity": "标准",
            },
            headers={"X-User-Id": user},
        )

    def test_each_card_matches_estimate_and_created_plan(self):
        for index, (path_id, card) in enumerate(self.cards.items()):
            with self.subTest(path_id=path_id):
                est = self._estimate(path_id, user=f"path-est-{index}")
                self.assertEqual(est.status_code, 200)
                estimate = est.json()
                self.assertEqual(estimate["knowledge_count"], card["knowledge_count"])
                self.assertEqual(estimate["recommended_days"], card["days"])
                self.assertEqual(estimate["target_days"], card["target_days"])
                self.assertEqual(estimate["target"]["type"], "path")

                created = self.client.post(
                    "/api/learning/plans",
                    json={
                        "path_id": path_id,
                        "current_level": "基础",
                        "daily_minutes": 30,
                        "intensity": "标准",
                        "selected_days": card["days"],
                    },
                    headers={"X-User-Id": f"path-plan-{index}"},
                )
                self.assertEqual(created.status_code, 201)
                plan = created.json()
                self.assertEqual(plan["total_knowledge_points"], card["knowledge_count"])
                self.assertEqual(plan["selected_days"], card["days"])
                self.assertEqual(plan["target_type"], "path")
                self.assertEqual(plan["target_id"], path_id)
                self.assertEqual(len(plan["days"]), card["days"])

    def test_no_last_day_dump(self):
        card = self.cards["ai-pm-sprint"]
        plan = self.client.post(
            "/api/learning/plans",
            json={
                "path_id": "ai-pm-sprint",
                "current_level": "基础",
                "daily_minutes": 30,
                "intensity": "标准",
                "selected_days": card["days"],
            },
            headers={"X-User-Id": "path-dump"},
        ).json()
        day_minutes = [d["planned_minutes"] for d in plan["days"]]
        self.assertTrue(all(m > 0 for m in day_minutes), f"存在空 Day：{day_minutes}")
        # 40 个知识点排 14 天时旧实现最后一天 260 分钟；现在应接近平均值。
        self.assertLessEqual(max(day_minutes), 80)
        self.assertGreater(min(day_minutes), 0)

    def test_level_changes_knowledge_count(self):
        def estimate(level):
            return self.client.post(
                "/api/learning/plans/estimate",
                json={
                    "path_id": "ai-pm-sprint",
                    "current_level": level,
                    "daily_minutes": 30,
                    "intensity": "标准",
                },
                headers={"X-User-Id": "path-level"},
            ).json()

        beginner = estimate("入门")
        advanced = estimate("进阶")
        self.assertLess(beginner["knowledge_count"], advanced["knowledge_count"])
        self.assertNotEqual(beginner["difficulty_counts"], advanced["difficulty_counts"])
        self.assertNotIn("高级", beginner["difficulty_counts"])

    def test_low_daily_minutes_never_creates_empty_days(self):
        data = self.client.post(
            "/api/learning/plans/estimate",
            json={
                "path_id": "ai-pm-sprint",
                "current_level": "基础",
                "daily_minutes": 15,
                "intensity": "标准",
            },
            headers={"X-User-Id": "path-low-daily"},
        ).json()
        self.assertLessEqual(data["recommended_days"], data["knowledge_count"])
        created = self.client.post(
            "/api/learning/plans",
            json={
                "path_id": "ai-pm-sprint",
                "current_level": "基础",
                "daily_minutes": 15,
                "intensity": "标准",
                "selected_days": data["recommended_days"],
            },
            headers={"X-User-Id": "path-low-daily-plan"},
        ).json()
        self.assertTrue(all(d["tasks"] for d in created["days"]))

    def test_intensity_changes_days_and_effective_minutes(self):
        def estimate(intensity):
            return self.client.post(
                "/api/learning/plans/estimate",
                json={
                    "path_id": "ai-pm-sprint",
                    "current_level": "基础",
                    "daily_minutes": 30,
                    "intensity": intensity,
                },
                headers={"X-User-Id": "path-intensity"},
            ).json()

        light = estimate("轻量")
        standard = estimate("标准")
        heavy = estimate("高强度")
        self.assertEqual(light["effective_daily_minutes"], 25)
        self.assertEqual(standard["effective_daily_minutes"], 30)
        self.assertEqual(heavy["effective_daily_minutes"], 40)
        self.assertGreater(light["recommended_days"], standard["recommended_days"])
        self.assertGreater(standard["recommended_days"], heavy["recommended_days"])

    def test_path_via_target_type_compat(self):
        resp = self.client.post(
            "/api/learning/plans/estimate",
            json={
                "target_type": "path",
                "target_id": "ai-pm-sprint",
                "current_level": "基础",
                "daily_minutes": 30,
                "intensity": "标准",
            },
            headers={"X-User-Id": "path-compat"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["target"]["type"], "path")

    def test_unknown_path_404(self):
        resp = self.client.post(
            "/api/learning/plans/estimate",
            json={"path_id": "nope", "current_level": "基础", "daily_minutes": 30, "intensity": "标准"},
            headers={"X-User-Id": "path-404"},
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["error"]["code"], "LEARNING_TARGET_NOT_FOUND")

    def test_missing_target_422(self):
        resp = self.client.post(
            "/api/learning/plans/estimate",
            json={"current_level": "基础", "daily_minutes": 30, "intensity": "标准"},
            headers={"X-User-Id": "path-422"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_custom_target_still_works(self):
        resp = self.client.post(
            "/api/learning/plans/estimate",
            json={
                "target_type": "category",
                "target_id": "ai-product",
                "current_level": "基础",
                "daily_minutes": 30,
                "intensity": "标准",
            },
            headers={"X-User-Id": "path-custom"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["target"]["type"], "category")
        self.assertGreater(data["knowledge_count"], 0)
        self.assertIsNone(data["path_id"])


class TestDistribute(unittest.TestCase):
    def test_even_distribution_without_last_day_dump(self):
        points = [_point(i) for i in range(40)]
        days = distribute(points, 30, 14)
        self.assertEqual(len(days), 14)
        loads = [sum(p.estimated_minutes for p in day) for day in days]
        self.assertTrue(all(load > 0 for load in loads))
        self.assertLessEqual(max(loads), 80)
        self.assertEqual(sum(loads), 800)

    def test_more_days_than_points(self):
        points = [_point(i) for i in range(3)]
        days = distribute(points, 30, 7)
        self.assertEqual(len(days), 7)
        self.assertEqual(sum(1 for day in days if day), 3)


if __name__ == "__main__":
    unittest.main()
