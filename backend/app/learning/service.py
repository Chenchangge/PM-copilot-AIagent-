"""Learning Plan 核心服务（Step 12-3 Part B）。

职责边界（§33）：
- Backend（确定性）：目标范围解析、draft/deprecated 过滤、依赖拓扑排序、学习量计算、
  日期排课、进度计算、完成状态计算。
- AI（可选、非单点故障）：学习周期解释 / 学习重点 / 学习建议；AI 不可用时回退确定性文案。

进度一致性（§35）：progress 一律由后端按 task 状态重算，前端只提交 task 完成。
"""
from __future__ import annotations

import json
import math
from collections import Counter
from functools import lru_cache

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.learning.constants import (
    CATEGORY_INTERVIEW_TYPES,
    CATEGORY_NAMES,
    CURRENT_LEVELS,
    DAILY_MINUTES_OPTIONS,
    DAY_CHOICES,
    DIFFICULTIES,
    DIRECTION_CATEGORIES,
    DIRECTIONS,
    INTENSITIES,
    INTERVIEW_RECOMMEND_RATIO,
    KNOWLEDGE_CATEGORIES,
    KNOWLEDGE_TOPICS,
    LEARNING_PATHS,
    LEARNING_PATHS_BY_ID,
    LEGACY_CATEGORY_LABELS,
    LEGACY_KNOWLEDGE_TITLES,
    PLAN_ACTIVE,
    PLAN_COMPLETED,
    PLAN_FEATURED_CATEGORIES,
    PLAN_PAUSED,
    RECORD_COMPLETED,
    RECORD_STARTED,
    TARGET_TYPE_CATEGORY,
    TARGET_TYPE_DIRECTION,
    TARGET_TYPE_PATH,
    TARGET_TYPE_TAG,
    TARGET_TYPE_TOPIC,
    TASK_COMPLETED,
    TASK_IN_PROGRESS,
    TASK_PENDING,
    TASK_SKIPPED,
    TOPIC_CATEGORY,
    TOPIC_NAMES,
)
from app.learning.errors import LearningError, LearningErrorCode
from app.learning.knowledge_index import (
    KnowledgePointView,
    build_knowledge_index,
    resolve_path,
    resolve_target,
)
from app.learning.planner import (
    compute_recommended_days,
    compute_total_minutes,
    distribute,
    effective_daily_minutes,
    filter_by_level,
    filter_recommendable,
    schedule_points,
)
from app.models.interview import InterviewEvaluation
from app.models.learning import KnowledgeLearningRecord, LearningPlan, LearningPlanDay, LearningPlanTask
from app.models.taxonomy import QuestionKnowledge
from app.schemas.learning import (
    CategoryOut,
    CreatePlanRequest,
    DayOut,
    EstimateRequest,
    EstimateResult,
    HomeSummaryOut,
    MakeupResult,
    PlanCategoryOut,
    PlanDetailOut,
    PlanListItem,
    PlanListResponse,
    PlanPathOut,
    PlanTaxonomyOut,
    PlanTopicOut,
    PrerequisiteInfo,
    RecommendedInterview,
    TargetInfo,
    TaskOut,
    TaxonomyOut,
    TodayProgress,
    TopicOut,
    UpdatePlanRequest,
)

QUESTIONS_FILE = PROJECT_ROOT / "interview" / "data" / "questions.json"


@lru_cache(maxsize=1)
def _question_type_counts() -> dict[str, int]:
    """题库 type → 题数（路径卡「高频题 N 道」用）。题库静态，进程内缓存。"""
    try:
        data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    return dict(Counter(q.get("type") for q in data if isinstance(q, dict) and q.get("type")))


def _difficulty_counts(points: list[KnowledgePointView]) -> dict[str, int]:
    counts = Counter(p.difficulty for p in points)
    return {d: counts[d] for d in DIFFICULTIES if counts.get(d)}


def _question_count(interview_types: list[str]) -> int:
    counts = _question_type_counts()
    return sum(counts.get(t, 0) for t in interview_types)


_INDEX: dict[str, KnowledgePointView] | None = None


def get_knowledge_index() -> dict[str, KnowledgePointView]:
    """进程内缓存的知识点索引（Markdown 源）。"""
    global _INDEX
    if _INDEX is None:
        _INDEX = build_knowledge_index()
    return _INDEX


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


class LearningService:
    def __init__(
        self,
        db: Session,
        llm_adapter=None,
        knowledge_index: dict[str, KnowledgePointView] | None = None,
    ) -> None:
        self.db = db
        self._llm = llm_adapter  # 测试注入；生产为 None
        self.index = knowledge_index if knowledge_index is not None else get_knowledge_index()

    # ================= 分类体系 =================
    def get_taxonomy(self) -> TaxonomyOut:
        """返回最终 taxonomy（11 分类 → 22 二级主题 → Tag），供学习计划目标选择。

        兼容路径：不带 scope 时保持原行为（知识库页 / 旧调用方仍可拿到全量 tags）。
        计划页请使用 get_plan_taxonomy()，不会收到 640 个标签。
        """
        categories = [CategoryOut(id=slug, name=name) for slug, name in KNOWLEDGE_CATEGORIES]
        topics = [
            TopicOut(id=slug, name=name, category_id=category_slug)
            for category_slug, slug, name in KNOWLEDGE_TOPICS
        ]
        tags = sorted({t for p in self.index.values() for t in p.tags})
        return TaxonomyOut(
            directions=list(DIRECTIONS),
            categories=categories,
            topics=topics,
            tags=tags,
            levels=list(CURRENT_LEVELS),
            daily_minutes=list(DAILY_MINUTES_OPTIONS),
            intensities=list(INTENSITIES),
            day_choices=list(DAY_CHOICES),
        )

    def get_plan_taxonomy(
        self,
        user_id: str,
        current_level: str,
        daily_minutes: int,
        intensity: str,
    ) -> PlanTaxonomyOut:
        """学习计划页专用精简 taxonomy（P0-1）。

        - 3 张路径卡：天数/知识点数/题数全部由后端按当前水平、每日时长、强度计算；
        - 分类 11 个，其中 5 个 featured；专题按分类分组下发（不扁平）；
        - 不下发 tags 全量，只返回最近一次面试评价导出的 ≤3 个薄弱标签。
        """
        paths = [
            self._path_card(path, current_level, daily_minutes, intensity)
            for path in LEARNING_PATHS
        ]

        category_rows: list[PlanCategoryOut] = []
        topics_by_category: dict[str, list[PlanTopicOut]] = {}
        for category_slug, category_name in KNOWLEDGE_CATEGORIES:
            points = filter_by_level(
                filter_recommendable(resolve_target(self.index, TARGET_TYPE_CATEGORY, category_slug)),
                current_level,
            )
            topic_rows: list[PlanTopicOut] = []
            for topic_category, topic_slug, topic_name in KNOWLEDGE_TOPICS:
                if topic_category != category_slug:
                    continue
                topic_points = filter_by_level(
                    filter_recommendable(resolve_target(self.index, TARGET_TYPE_TOPIC, topic_slug)),
                    current_level,
                )
                topic_rows.append(
                    PlanTopicOut(
                        id=topic_slug,
                        name=topic_name,
                        category_id=category_slug,
                        knowledge_count=len(topic_points),
                    )
                )
            topics_by_category[category_slug] = topic_rows
            category_rows.append(
                PlanCategoryOut(
                    id=category_slug,
                    name=category_name,
                    knowledge_count=len(points),
                    topic_count=len(topic_rows),
                    featured=category_slug in PLAN_FEATURED_CATEGORIES,
                )
            )

        # featured 按产品定义顺序，其余按知识点数量降序（数量相同时保持分类定义顺序）。
        order = {slug: i for i, slug in enumerate(PLAN_FEATURED_CATEGORIES)}
        category_rows.sort(
            key=lambda c: (
                0 if c.featured else 1,
                order.get(c.id, 999) if c.featured else -c.knowledge_count,
            )
        )

        return PlanTaxonomyOut(
            paths=paths,
            categories=category_rows,
            topics=topics_by_category,
            directions=list(DIRECTIONS),
            levels=list(CURRENT_LEVELS),
            daily_minutes=list(DAILY_MINUTES_OPTIONS),
            intensities=list(INTENSITIES),
            recommended_tags=self._recommended_tags(user_id),
            current_level=current_level,
            selected_daily_minutes=daily_minutes,
            selected_intensity=intensity,
        )

    def _path_card(
        self,
        path: dict,
        current_level: str,
        daily_minutes: int,
        intensity: str,
    ) -> PlanPathOut:
        points = self._path_points(path, current_level)
        total_minutes = compute_total_minutes(points)
        effective = effective_daily_minutes(daily_minutes, intensity)
        days = self._path_days(path, points, total_minutes, effective)
        return PlanPathOut(
            id=path["id"],
            name=path["name"],
            subtitle=path["subtitle"],
            days=days,
            target_days=path["days_hint"],
            knowledge_count=len(points),
            question_count=_question_count(path.get("interview_types", [])),
            effective_daily_minutes=effective,
            difficulty_counts=_difficulty_counts(points),
            target_type=path["target_type"],
            target_ids=list(path["target_ids"]),
        )

    def _path_points(self, path: dict, current_level: str) -> list[KnowledgePointView]:
        points = filter_recommendable(resolve_path(self.index, path))
        return filter_by_level(points, current_level)

    @staticmethod
    def _path_days(
        path: dict,
        points: list[KnowledgePointView],
        total_minutes: int,
        effective_minutes: int,
    ) -> int:
        """路径实际天数：不短于建议冲刺周期，也不长于知识点数量（每天至少 1 个任务）。

        - 入门档知识点变少时，用 min(days_hint, 知识点数) 兜底，避免空 Day；
        - 每日时长很低（如 15 分钟）时，required 可能大于知识点数，再按知识点数封顶，
          否则会出现「本日暂无任务」的 Day（P2-1 的同类问题）。
        """
        if not points:
            return 0
        required = compute_recommended_days(total_minutes, effective_minutes)
        target = min(path["days_hint"], len(points))
        return min(len(points), max(required, target))

    def _core_relation_counts(self) -> dict[str, int]:
        """核心题关联次数：用于「核心速成」优先选真正被面试题覆盖的知识点。"""
        try:
            rows = self.db.execute(
                select(QuestionKnowledge.knowledge_point_id).where(
                    QuestionKnowledge.relation_type == "core"
                )
            ).scalars().all()
        except SQLAlchemyError:
            return {}
        return dict(Counter(rows))

    def _crash_points(
        self,
        points: list[KnowledgePointView],
        daily_minutes: int,
        intensity: str,
    ) -> list[KnowledgePointView]:
        """核心速成：只选被 core 题目覆盖的知识点，并按 14 天预算截断。

        没有 core 关系（旧库/测试库）时退回全部候选项，但仍受 14 天预算约束。
        """
        effective = effective_daily_minutes(daily_minutes, intensity)
        budget = 14 * effective
        counts = self._core_relation_counts()
        core = [p for p in points if counts.get(p.id, 0) > 0]
        candidates = core or points
        candidates = sorted(
            candidates,
            key=lambda p: (-counts.get(p.id, 0), p.estimated_minutes, p.title),
        )
        selected: list[KnowledgePointView] = []
        total = 0
        for point in candidates:
            if selected and total + point.estimated_minutes > budget:
                continue
            selected.append(point)
            total += point.estimated_minutes
            if total >= budget:
                break
        return selected or points[:1]

    @staticmethod
    def _crash_days(points: list[KnowledgePointView], total_minutes: int, effective_minutes: int) -> int:
        return max(1, min(14, compute_recommended_days(total_minutes, effective_minutes), len(points)))

    # ================= estimate =================
    def estimate(self, user_id: str, req: EstimateRequest) -> EstimateResult:
        ordered, target_name, path = self._resolve_ordered(req)
        total_minutes = compute_total_minutes(ordered)
        effective_minutes = effective_daily_minutes(req.daily_minutes, req.intensity)
        if getattr(req, "mode", "full") == "crash":
            recommended_days = self._crash_days(ordered, total_minutes, effective_minutes)
        elif path is not None:
            recommended_days = self._path_days(path, ordered, total_minutes, effective_minutes)
        else:
            # 天数不能超过知识点数，否则最后几天必然空（每天至少 1 个任务）。
            recommended_days = min(
                compute_recommended_days(total_minutes, effective_minutes), len(ordered)
            )

        key_topics = [p.title for p in ordered[:6]]
        explanation = self._ai_explain(
            user_id,
            {
                "target_name": target_name,
                "knowledge_count": len(ordered),
                "total_minutes": total_minutes,
                "daily_minutes": req.daily_minutes,
                "effective_minutes": effective_minutes,
                "intensity": req.intensity,
                "recommended_days": recommended_days,
                "current_level": req.current_level,
                "direction": req.direction_id,
                "key_topics": key_topics,
            },
        )
        # 可选天数不超过知识点数：否则必然出现「本日暂无任务」的空 Day。
        day_choices = sorted(
            {d for d in [recommended_days] + list(DAY_CHOICES) if d <= len(ordered)}
        )

        return EstimateResult(
            target=TargetInfo(
                type=TARGET_TYPE_PATH if path is not None else req.target_type,
                id=path["id"] if path is not None else req.target_id,
                name=target_name,
            ),
            path_id=path["id"] if path is not None else None,
            target_days=path["days_hint"] if path is not None else None,
            mode=getattr(req, "mode", "full"),
            knowledge_count=len(ordered),
            total_minutes=total_minutes,
            recommended_days=recommended_days,
            recommended_daily_minutes=req.daily_minutes,
            effective_daily_minutes=effective_minutes,
            recommended_tasks_per_day=max(1, math.ceil(len(ordered) / recommended_days)),
            difficulty_counts=_difficulty_counts(ordered),
            key_topics=key_topics,
            prerequisites=self._prerequisites(ordered),
            explanation=explanation,
            day_choices=day_choices,
        )

    # ================= 创建 / 查询计划 =================
    def create_plan(self, user_id: str, req: CreatePlanRequest) -> PlanDetailOut:
        ordered, target_name, path = self._resolve_ordered(req)
        total_minutes = compute_total_minutes(ordered)
        effective_minutes = effective_daily_minutes(req.daily_minutes, req.intensity)
        if getattr(req, "mode", "full") == "crash":
            recommended_days = self._crash_days(ordered, total_minutes, effective_minutes)
        elif path is not None:
            recommended_days = self._path_days(path, ordered, total_minutes, effective_minutes)
        else:
            recommended_days = min(
                compute_recommended_days(total_minutes, effective_minutes), len(ordered)
            )
        selected_days = req.selected_days if req.selected_days > 0 else recommended_days
        if getattr(req, "mode", "full") == "crash":
            selected_days = min(14, selected_days)
        # 没有足够知识点时裁剪天数，避免生成「本日暂无任务」的空 Day。
        selected_days = max(1, min(selected_days, len(ordered)))

        # 路径计划自动带上面试方向（用于完成后的模拟面试推荐）。
        direction_id = req.direction_id or (path.get("direction") if path else None)
        target_type = TARGET_TYPE_PATH if path is not None else req.target_type
        target_id = path["id"] if path is not None else req.target_id

        days = distribute(ordered, effective_minutes, selected_days)

        plan = LearningPlan(
            user_id=user_id,
            title=req.title or self._default_title(target_type, target_name, direction_id),
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            direction_id=direction_id,
            current_level=req.current_level,
            daily_minutes=req.daily_minutes,
            intensity=req.intensity,
            recommended_days=recommended_days,
            selected_days=selected_days,
            total_knowledge_points=len(ordered),
            total_estimated_minutes=total_minutes,
            completed_knowledge_points=0,
            completed_minutes=0,
            progress_percent=0,
            status=PLAN_ACTIVE,
            started_at=_utcnow(),
        )
        self.db.add(plan)
        self.db.flush()

        for i, day_points in enumerate(days, start=1):
            day = LearningPlanDay(
                plan_id=plan.id,
                day_number=i,
                planned_minutes=sum(p.estimated_minutes for p in day_points),
                completed_minutes=0,
                progress_percent=0,
                status="in_progress" if i == 1 else "available",
            )
            self.db.add(day)
            self.db.flush()
            for p in day_points:
                self.db.add(
                    LearningPlanTask(
                        plan_day_id=day.id,
                        knowledge_point_id=p.id,
                        estimated_minutes=p.estimated_minutes,
                        status=TASK_PENDING,
                    )
                )
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    def list_plans(self, user_id: str) -> PlanListResponse:
        rows = self.db.execute(
            select(LearningPlan)
            .where(LearningPlan.user_id == user_id)
            .order_by(LearningPlan.created_at.desc())
        ).scalars().all()
        return PlanListResponse(items=[self._plan_item(p) for p in rows])

    def get_plan(self, user_id: str, plan_id: int) -> PlanDetailOut:
        return self._plan_detail(self._get_plan(user_id, plan_id))

    def pause(self, user_id: str, plan_id: int) -> PlanDetailOut:
        plan = self._get_plan(user_id, plan_id)
        if plan.status != PLAN_ACTIVE:
            raise LearningError(LearningErrorCode.learning_plan_state, "当前状态不允许暂停")
        plan.status = PLAN_PAUSED
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    def resume(self, user_id: str, plan_id: int) -> PlanDetailOut:
        plan = self._get_plan(user_id, plan_id)
        if plan.status != PLAN_PAUSED:
            raise LearningError(LearningErrorCode.learning_plan_state, "当前状态不允许恢复")
        plan.status = PLAN_ACTIVE
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    def update_plan(self, user_id: str, plan_id: int, req: UpdatePlanRequest) -> PlanDetailOut:
        plan = self._get_plan(user_id, plan_id)
        if plan.status not in (PLAN_ACTIVE, PLAN_PAUSED):
            raise LearningError(LearningErrorCode.learning_plan_state, "当前状态不允许调整")
        new_daily = req.daily_minutes if req.daily_minutes is not None else plan.daily_minutes
        new_days = req.selected_days if req.selected_days is not None else plan.selected_days
        if req.intensity is not None:
            plan.intensity = req.intensity
        plan.daily_minutes = new_daily
        plan.selected_days = new_days
        effective_minutes = effective_daily_minutes(new_daily, plan.intensity)
        self._reschedule_remaining(plan, effective_minutes, new_days)
        self._recompute_plan(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    # ================= 任务 =================
    def start_task(self, user_id: str, task_id: int) -> TaskOut:
        task, plan = self._get_task(user_id, task_id)
        if task.status == TASK_COMPLETED:
            raise LearningError(LearningErrorCode.learning_task_state, "任务已完成")
        if task.status == TASK_SKIPPED:
            raise LearningError(LearningErrorCode.learning_task_state, "任务已跳过")
        if task.status == TASK_PENDING:
            task.status = TASK_IN_PROGRESS
        day = self.db.get(LearningPlanDay, task.plan_day_id)
        if day is not None and day.status == "available":
            day.status = "in_progress"
        if plan.started_at is None:
            plan.started_at = _utcnow()
        self._ensure_record(user_id, plan, task)
        self.db.commit()
        return self._task_out(task)

    def complete_task(self, user_id: str, task_id: int) -> PlanDetailOut:
        task, plan = self._get_task(user_id, task_id)
        if task.status == TASK_COMPLETED:
            return self._plan_detail(plan)  # 幂等
        if task.status == TASK_SKIPPED:
            raise LearningError(LearningErrorCode.learning_task_state, "已跳过的任务无法完成")
        task.status = TASK_COMPLETED
        task.completed_at = _utcnow()
        self._complete_record(user_id, plan, task)
        self._recompute_plan(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    def skip_task(self, user_id: str, task_id: int) -> PlanDetailOut:
        task, plan = self._get_task(user_id, task_id)
        if task.status == TASK_COMPLETED:
            raise LearningError(LearningErrorCode.learning_task_state, "已完成的任务不能跳过")
        if task.status == TASK_SKIPPED:
            return self._plan_detail(plan)  # 幂等
        task.status = TASK_SKIPPED
        task.completed_at = _utcnow()
        self._recompute_plan(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    # ================= 补卡 =================
    def makeup(self, user_id: str, plan_id: int) -> MakeupResult:
        """把昨天未完成（pending / in_progress）的任务平移到今天。"""
        plan = self._get_plan(user_id, plan_id)
        if plan.status not in (PLAN_ACTIVE, PLAN_PAUSED):
            raise LearningError(LearningErrorCode.learning_plan_state, "当前状态不允许补卡")

        days, tasks_by_day = self._load_days(plan)
        current_number = self._current_day_number(days)
        today = next((d for d in days if d.day_number == current_number), None)
        yesterday = next((d for d in days if d.day_number == current_number - 1), None)
        if today is None or yesterday is None:
            return MakeupResult(moved=0, plan=self._plan_detail(plan))

        moving = [
            t for t in tasks_by_day.get(yesterday.id, [])
            if t.status in (TASK_PENDING, TASK_IN_PROGRESS)
        ]
        for task in moving:
            task.plan_day_id = today.id
        if moving:
            self._recompute_plan(plan)
            self.db.commit()
            self.db.refresh(plan)
        return MakeupResult(moved=len(moving), plan=self._plan_detail(plan))

    # ================= 独立学习记录 =================
    def start_knowledge(self, user_id: str, knowledge_id: str) -> dict:
        self._require_knowledge(knowledge_id)
        rec = self._standalone_record(user_id, knowledge_id)
        if rec is None:
            self.db.add(
                KnowledgeLearningRecord(
                    user_id=user_id,
                    knowledge_point_id=knowledge_id,
                    status=RECORD_STARTED,
                    started_at=_utcnow(),
                )
            )
        elif rec.status != RECORD_STARTED:
            rec.status = RECORD_STARTED
            rec.started_at = rec.started_at or _utcnow()
        self.db.commit()
        return {"knowledge_point_id": knowledge_id, "status": RECORD_STARTED}

    def complete_knowledge(self, user_id: str, knowledge_id: str, actual_minutes: int | None = None) -> dict:
        self._require_knowledge(knowledge_id)
        rec = self._standalone_record(user_id, knowledge_id)
        now = _utcnow()
        if rec is None:
            self.db.add(
                KnowledgeLearningRecord(
                    user_id=user_id,
                    knowledge_point_id=knowledge_id,
                    status=RECORD_COMPLETED,
                    started_at=now,
                    completed_at=now,
                    actual_minutes=actual_minutes,
                )
            )
        else:
            rec.status = RECORD_COMPLETED
            rec.started_at = rec.started_at or now
            rec.completed_at = now
            if actual_minutes is not None:
                rec.actual_minutes = actual_minutes
        self.db.commit()
        return {"knowledge_point_id": knowledge_id, "status": RECORD_COMPLETED}

    # ================= 首页摘要 =================
    def home_summary(self, user_id: str) -> HomeSummaryOut:
        plan = self._current_plan(user_id)
        if plan is None:
            return HomeSummaryOut(active_plan=None, overall_progress=0, recommended_next_action="start")
        days, tasks_by_day = self._load_days(plan)
        day_number = self._current_day_number(days)
        day = next((d for d in days if d.day_number == day_number), None)
        today_tasks = tasks_by_day.get(day.id, []) if day else []
        active_today = [t for t in today_tasks if t.status != TASK_SKIPPED]
        done = sum(1 for t in active_today if t.status == TASK_COMPLETED)
        minutes = sum(t.estimated_minutes for t in active_today if t.status == TASK_COMPLETED)

        next_action = "continue"
        if plan.status == PLAN_COMPLETED:
            next_action = "interview"
        elif active_today and done == len(active_today):
            next_action = "day_done"

        return HomeSummaryOut(
            active_plan=self._plan_item(plan),
            today_tasks=[self._task_out(t) for t in today_tasks],
            overall_progress=plan.progress_percent,
            today_progress=TodayProgress(done=done, total=len(active_today), minutes=minutes),
            recommended_next_action=next_action,
        )

    # ================= 内部：目标解析 =================
    def _resolve_ordered(self, req) -> tuple[list[KnowledgePointView], str, dict | None]:
        """解析目标 → 按当前水平过滤 → 依赖拓扑排序。

        返回 (ordered, target_name, path)。path 仅在 path_id 入口时非空。
        """
        path: dict | None = None
        path_id = req.path_id or (req.target_id if req.target_type == TARGET_TYPE_PATH else None)
        if path_id:
            path = LEARNING_PATHS_BY_ID.get(path_id)
            if path is None:
                raise LearningError(
                    LearningErrorCode.learning_target_not_found,
                    f"学习路径不存在：{path_id}",
                )
            target_name = path["name"]
            points = filter_recommendable(resolve_path(self.index, path))
        else:
            target_name = self._target_name(req.target_type, req.target_id)
            points = filter_recommendable(resolve_target(self.index, req.target_type, req.target_id))

        points = filter_by_level(points, req.current_level)
        if getattr(req, "mode", "full") == "crash":
            points = self._crash_points(points, req.daily_minutes, req.intensity)
        if not points:
            raise LearningError(
                LearningErrorCode.learning_target_empty,
                f"该目标下没有可学习的内容：{target_name}",
            )
        return schedule_points(points), target_name, path

    def _target_name(self, target_type: str, target_id: str) -> str:
        if target_type == TARGET_TYPE_PATH:
            path = LEARNING_PATHS_BY_ID.get(target_id)
            return path["name"] if path is not None else target_id
        if target_type == TARGET_TYPE_TAG:
            return target_id
        if target_type == TARGET_TYPE_DIRECTION:
            return target_id  # 方向中文名即目标名
        if target_type == TARGET_TYPE_TOPIC:
            return TOPIC_NAMES.get(target_id, LEGACY_CATEGORY_LABELS.get(target_id, target_id))
        return CATEGORY_NAMES.get(target_id, LEGACY_CATEGORY_LABELS.get(target_id, target_id))

    def _default_title(self, target_type: str, target_name: str, direction: str | None) -> str:
        # 路径名本身已经是完整产品名，不再拼「学习计划」后缀。
        if target_type == TARGET_TYPE_PATH:
            return target_name
        # direction 本身作为目标时不重复加方向前缀
        if target_type == TARGET_TYPE_DIRECTION:
            return f"{target_name} 学习计划"
        prefix = f"{direction} · " if direction else ""
        return f"{prefix}{target_name} 学习计划"

    def _prerequisites(self, ordered: list[KnowledgePointView]) -> list[PrerequisiteInfo]:
        ids = {p.id for p in ordered}
        seen: set[str] = set()
        out: list[PrerequisiteInfo] = []
        for p in ordered:
            for dep in p.dependencies:
                if dep in ids or dep in seen:
                    continue
                seen.add(dep)
                doc = self.index.get(dep)
                out.append(PrerequisiteInfo(id=dep, title=doc.title if doc else dep))
        return out

    # ================= 内部：AI 解释（可选） =================
    def _ai_explain(self, user_id: str, ctx: dict) -> str:
        fallback = (
            f"目标「{ctx['target_name']}」在「{ctx.get('current_level', '基础')}」水平下共 "
            f"{ctx['knowledge_count']} 个知识点、约 {ctx['total_minutes']} 分钟。"
            f"每日 {ctx['daily_minutes']} 分钟、{ctx.get('intensity', '标准')}强度，"
            f"折算每日有效 {ctx.get('effective_minutes', ctx['daily_minutes'])} 分钟，"
            f"建议 {ctx['recommended_days']} 天完成。"
        )
        text = self._generate_explanation(user_id, ctx)
        return (text or "").strip()[:800] if text else fallback

    def _generate_explanation(self, user_id: str, ctx: dict) -> str | None:
        """尝试用 AI 生成学习周期解释；失败/无模型返回 None（非单点故障）。"""
        if self._llm is not None:
            adapter = self._llm
        else:
            from app.services.model_service import ModelService

            model = ModelService(self.db).find_text_generation_model(user_id)
            if model is None:
                return None
            from app.services.providers import get_adapter
            from app.services.secret_storage import secret_storage

            try:
                adapter = get_adapter(
                    model.provider,
                    model.base_url or "",
                    secret_storage.unseal(model.api_key_secret),
                    model.model,
                )
            except Exception:  # noqa: BLE001
                return None
        try:
            messages = [
                {"role": "system", "content": "你是学习规划助手，用 2-3 句话简要解释学习周期与建议，不要输出列表。"},
                {"role": "user", "content": self._explain_prompt(ctx)},
            ]
            result = adapter.generate(messages, options={"temperature": 0})
        except Exception:  # noqa: BLE001 - 超时/JSON/网络等一律回退，不阻断
            return None
        return result.get("content") or None

    @staticmethod
    def _explain_prompt(ctx: dict) -> str:
        return (
            f"学习目标：{ctx['target_name']}；知识点数：{ctx['knowledge_count']}；"
            f"总时长：{ctx['total_minutes']} 分钟；每日：{ctx['daily_minutes']} 分钟；"
            f"强度：{ctx.get('intensity', '标准')}；折算每日有效：{ctx.get('effective_minutes', ctx['daily_minutes'])} 分钟；"
            f"推荐周期：{ctx['recommended_days']} 天；当前水平：{ctx.get('current_level', '未指定')}；"
            f"目标方向：{ctx.get('direction') or '未指定'}；学习重点：{'、'.join(ctx.get('key_topics', []))}。"
        )

    # ================= 内部：排期 =================
    def _reschedule_remaining(self, plan: LearningPlan, daily_minutes: int, selected_days: int) -> None:
        """重新排期：已完成任务保持原 Day 不动；未完成任务重新分配（§32）。"""
        days, tasks_by_day = self._load_days(plan)
        all_tasks = [t for tasks in tasks_by_day.values() for t in tasks]
        pending_points = [
            self.index.get(t.knowledge_point_id)
            for t in all_tasks
            if t.status not in (TASK_COMPLETED, TASK_SKIPPED)
        ]
        pending_points = schedule_points([p for p in pending_points if p is not None])

        # 删除未完成任务（已完成/已跳过任务冻结在原 Day）
        for t in all_tasks:
            if t.status not in (TASK_COMPLETED, TASK_SKIPPED):
                self.db.delete(t)

        n = max(1, selected_days)
        new_days = distribute(pending_points, daily_minutes, n)
        for day_number, points in enumerate(new_days, start=1):
            day = self._day_by_number(plan, days, day_number)
            for p in points:
                self.db.add(
                    LearningPlanTask(
                        plan_day_id=day.id,
                        knowledge_point_id=p.id,
                        estimated_minutes=p.estimated_minutes,
                        status=TASK_PENDING,
                    )
                )

        # 补齐超出已有 Day 的空 Day
        for day_number in range(len(days) + 1, n + 1):
            self.db.add(LearningPlanDay(plan_id=plan.id, day_number=day_number, status="available"))
        self.db.flush()
        self._prune_empty_days(plan, n)

    def _prune_empty_days(self, plan: LearningPlan, max_days: int) -> None:
        days = self.db.execute(
            select(LearningPlanDay).where(LearningPlanDay.plan_id == plan.id)
        ).scalars().all()
        for d in days:
            if d.day_number <= max_days:
                continue
            cnt = self.db.execute(
                select(func.count(LearningPlanTask.id)).where(LearningPlanTask.plan_day_id == d.id)
            ).scalar() or 0
            if cnt == 0:
                self.db.delete(d)

    def _day_by_number(self, plan, days, day_number) -> LearningPlanDay:
        for d in days:
            if d.day_number == day_number:
                return d
        day = LearningPlanDay(plan_id=plan.id, day_number=day_number, status="available")
        self.db.add(day)
        self.db.flush()
        return day

    # ================= 内部：进度重算 =================
    def _recompute_plan(self, plan: LearningPlan) -> None:
        days, tasks_by_day = self._load_days(plan)
        all_tasks = [t for tasks in tasks_by_day.values() for t in tasks]

        # 跳过（已掌握）的任务从完成率分母中剔除，但不能让进度倒退。
        active_tasks = [t for t in all_tasks if t.status != TASK_SKIPPED]
        plan.total_knowledge_points = len(active_tasks)
        plan.total_estimated_minutes = sum(t.estimated_minutes for t in active_tasks)
        completed = [t for t in active_tasks if t.status == TASK_COMPLETED]
        plan.completed_knowledge_points = len(completed)
        plan.completed_minutes = sum(t.estimated_minutes for t in completed)
        if not active_tasks:
            plan.progress_percent = 100 if all_tasks else 0
        else:
            plan.progress_percent = round(len(completed) / len(active_tasks) * 100)
        if all_tasks and not active_tasks:
            plan.status = PLAN_COMPLETED
            plan.completed_at = plan.completed_at or _utcnow()
        elif active_tasks and len(completed) == len(active_tasks):
            plan.status = PLAN_COMPLETED
            plan.completed_at = plan.completed_at or _utcnow()

        days_by_id = {d.id: d for d in days}
        for day_id, tasks in tasks_by_day.items():
            day = days_by_id[day_id]
            active = [t for t in tasks if t.status != TASK_SKIPPED]
            planned = sum(t.estimated_minutes for t in active)
            done = sum(t.estimated_minutes for t in active if t.status == TASK_COMPLETED)
            day.planned_minutes = planned
            day.completed_minutes = done
            if tasks and all(t.status == TASK_SKIPPED for t in tasks):
                # 整日都是「已掌握」跳过的内容：显示已跳过，不伪造 100% 完成
                day.progress_percent = 0
                day.status = "skipped"
                continue
            day.progress_percent = round(done / planned * 100) if planned else (100 if tasks else 0)
            if tasks and all(t.status in (TASK_COMPLETED, TASK_SKIPPED) for t in tasks):
                day.status = "completed"
                day.completed_at = day.completed_at or _utcnow()
            elif any(t.status in (TASK_COMPLETED, TASK_IN_PROGRESS) for t in active):
                day.status = "in_progress"
            else:
                day.status = "available"

    # ================= 内部：查询 =================
    def _get_plan(self, user_id: str, plan_id: int) -> LearningPlan:
        plan = self.db.execute(
            select(LearningPlan).where(LearningPlan.id == plan_id, LearningPlan.user_id == user_id)
        ).scalars().first()
        if plan is None:
            raise LearningError(LearningErrorCode.learning_plan_not_found, "学习计划不存在")
        return plan

    def _current_plan(self, user_id: str) -> LearningPlan | None:
        return self.db.execute(
            select(LearningPlan)
            .where(LearningPlan.user_id == user_id, LearningPlan.status.in_([PLAN_ACTIVE, PLAN_PAUSED]))
            .order_by(LearningPlan.created_at.desc())
        ).scalars().first()

    def _get_task(self, user_id: str, task_id: int) -> tuple[LearningPlanTask, LearningPlan]:
        task = self.db.execute(
            select(LearningPlanTask)
            .join(LearningPlanDay, LearningPlanDay.id == LearningPlanTask.plan_day_id)
            .join(LearningPlan, LearningPlan.id == LearningPlanDay.plan_id)
            .where(LearningPlanTask.id == task_id, LearningPlan.user_id == user_id)
        ).scalars().first()
        if task is None:
            raise LearningError(LearningErrorCode.learning_task_not_found, "学习任务不存在")
        day = self.db.get(LearningPlanDay, task.plan_day_id)
        plan = self.db.get(LearningPlan, day.plan_id)
        return task, plan

    def _load_days(self, plan: LearningPlan):
        days = self.db.execute(
            select(LearningPlanDay)
            .where(LearningPlanDay.plan_id == plan.id)
            .order_by(LearningPlanDay.day_number)
        ).scalars().all()
        day_ids = [d.id for d in days]
        tasks = (
            self.db.execute(
                select(LearningPlanTask)
                .where(LearningPlanTask.plan_day_id.in_(day_ids))
                .order_by(LearningPlanTask.id)
            ).scalars().all()
            if day_ids
            else []
        )
        by_day: dict[int, list[LearningPlanTask]] = {}
        for t in tasks:
            by_day.setdefault(t.plan_day_id, []).append(t)
        return days, by_day

    def _current_day_number(self, days) -> int:
        for d in days:
            # 整日被跳过的内容等同于「这一天已处理完」，进度进入下一天
            if d.status not in ("completed", "skipped"):
                return d.day_number
        return days[-1].day_number if days else 1

    def _require_knowledge(self, knowledge_id: str) -> None:
        if knowledge_id not in self.index:
            raise LearningError(LearningErrorCode.learning_knowledge_not_found, "知识点不存在")

    def _standalone_record(self, user_id: str, knowledge_id: str) -> KnowledgeLearningRecord | None:
        return self.db.execute(
            select(KnowledgeLearningRecord).where(
                KnowledgeLearningRecord.user_id == user_id,
                KnowledgeLearningRecord.knowledge_point_id == knowledge_id,
                KnowledgeLearningRecord.plan_task_id.is_(None),
            )
        ).scalars().first()

    def _record_for_task(self, user_id: str, task: LearningPlanTask) -> KnowledgeLearningRecord | None:
        return self.db.execute(
            select(KnowledgeLearningRecord).where(
                KnowledgeLearningRecord.user_id == user_id,
                KnowledgeLearningRecord.plan_task_id == task.id,
            )
        ).scalars().first()

    def _ensure_record(self, user_id: str, plan: LearningPlan, task: LearningPlanTask) -> None:
        rec = self._record_for_task(user_id, task)
        if rec is None:
            self.db.add(
                KnowledgeLearningRecord(
                    user_id=user_id,
                    knowledge_point_id=task.knowledge_point_id,
                    plan_id=plan.id,
                    plan_task_id=task.id,
                    status=RECORD_STARTED,
                    started_at=_utcnow(),
                )
            )

    def _complete_record(self, user_id: str, plan: LearningPlan, task: LearningPlanTask) -> None:
        rec = self._record_for_task(user_id, task)
        now = _utcnow()
        if rec is None:
            self.db.add(
                KnowledgeLearningRecord(
                    user_id=user_id,
                    knowledge_point_id=task.knowledge_point_id,
                    plan_id=plan.id,
                    plan_task_id=task.id,
                    status=RECORD_COMPLETED,
                    started_at=now,
                    completed_at=now,
                    actual_minutes=task.estimated_minutes,
                )
            )
        else:
            rec.status = RECORD_COMPLETED
            rec.started_at = rec.started_at or now
            rec.completed_at = now
            rec.actual_minutes = task.estimated_minutes

    # ================= 序列化 =================
    def _task_out(self, t: LearningPlanTask) -> TaskOut:
        doc = self.index.get(t.knowledge_point_id)
        return TaskOut(
            id=t.id,
            knowledge_point_id=t.knowledge_point_id,
            title=doc.title if doc else LEGACY_KNOWLEDGE_TITLES.get(
                t.knowledge_point_id, t.knowledge_point_id
            ),
            category=doc.category if doc else "",
            difficulty=doc.difficulty if doc else "",
            estimated_minutes=t.estimated_minutes,
            status=t.status,
            completed_at=t.completed_at,
        )

    def _plan_item(self, plan: LearningPlan) -> PlanListItem:
        days, _ = self._load_days(plan)
        return PlanListItem(
            id=plan.id,
            title=plan.title,
            target_name=plan.target_name,
            status=plan.status,
            progress_percent=plan.progress_percent,
            selected_days=plan.selected_days,
            total_knowledge_points=plan.total_knowledge_points,
            completed_knowledge_points=plan.completed_knowledge_points,
            current_day_number=self._current_day_number(days),
            created_at=plan.created_at,
        )

    def _plan_detail(self, plan: LearningPlan) -> PlanDetailOut:
        days, tasks_by_day = self._load_days(plan)
        day_outs = [
            DayOut(
                id=d.id,
                day_number=d.day_number,
                planned_minutes=d.planned_minutes,
                completed_minutes=d.completed_minutes,
                progress_percent=d.progress_percent,
                status=d.status,
                tasks=[self._task_out(t) for t in tasks_by_day.get(d.id, [])],
            )
            for d in days
        ]
        return PlanDetailOut(
            id=plan.id,
            title=plan.title,
            target_type=plan.target_type,
            target_id=plan.target_id,
            target_name=plan.target_name,
            direction_id=plan.direction_id,
            direction_name=plan.direction_id,
            current_level=plan.current_level,
            daily_minutes=plan.daily_minutes,
            intensity=plan.intensity,
            recommended_days=plan.recommended_days,
            selected_days=plan.selected_days,
            total_knowledge_points=plan.total_knowledge_points,
            total_estimated_minutes=plan.total_estimated_minutes,
            completed_knowledge_points=plan.completed_knowledge_points,
            completed_minutes=plan.completed_minutes,
            progress_percent=plan.progress_percent,
            status=plan.status,
            current_day_number=self._current_day_number(days),
            created_at=plan.created_at,
            started_at=plan.started_at,
            completed_at=plan.completed_at,
            days=day_outs,
            recommended_interview=self._recommended_interview(plan),
        )

    def _recommended_tags(self, user_id: str) -> list[str]:
        """从最近一次完成的面试评价里取 ≤3 个薄弱标签（不再下发全量 tag）。

        优先用 recommended_knowledge（规则推荐的薄弱知识点）的第一批 tag；
        没有评价 / 推荐知识点没有 tag 时返回空列表，页面不渲染标签入口。
        """
        row = self.db.execute(
            select(InterviewEvaluation)
            .where(
                InterviewEvaluation.user_id == user_id,
                InterviewEvaluation.status == "completed",
            )
            .order_by(InterviewEvaluation.created_at.desc(), InterviewEvaluation.id.desc())
        ).scalars().first()
        if row is None:
            return []

        tags: list[str] = []
        for item in row.recommended_knowledge or []:
            if not isinstance(item, dict):
                continue
            doc = self.index.get(item.get("knowledge_id", ""))
            if doc is None:
                continue
            for tag in doc.tags:
                if tag in tags:
                    continue
                tags.append(tag)
                if len(tags) >= 3:
                    return tags
        return tags

    def _recommended_interview(self, plan: LearningPlan) -> RecommendedInterview | None:
        total = plan.total_knowledge_points
        if total == 0:
            return None
        ratio = plan.completed_knowledge_points / total
        if ratio < INTERVIEW_RECOMMEND_RATIO:
            return None
        category = self._target_category(plan)
        interview_type = CATEGORY_INTERVIEW_TYPES.get(category, "产品基础")
        knowledge_ids = [t.knowledge_point_id for t in self._all_tasks(plan) if t.status == TASK_COMPLETED]
        return RecommendedInterview(
            eligible=True,
            ratio=round(ratio, 3),
            direction=plan.direction_id,
            interview_type=interview_type,
            knowledge_ids=knowledge_ids,
        )

    def _target_category(self, plan: LearningPlan) -> str:
        if plan.target_type == TARGET_TYPE_PATH:
            path = LEARNING_PATHS_BY_ID.get(plan.target_id)
            if path is not None and path.get("target_ids"):
                first = path["target_ids"][0]
                if path["target_type"] == TARGET_TYPE_TOPIC:
                    return TOPIC_CATEGORY.get(first, first)
                return first
            return "product-foundation"
        if plan.target_type == TARGET_TYPE_CATEGORY:
            return plan.target_id
        if plan.target_type == TARGET_TYPE_TOPIC:
            return TOPIC_CATEGORY.get(plan.target_id, plan.target_id)
        if plan.target_type == TARGET_TYPE_DIRECTION:
            cats = DIRECTION_CATEGORIES.get(plan.target_id, [])
            return cats[0] if cats else plan.target_id
        for p in self.index.values():
            if plan.target_id in p.tags:
                return p.category
        return plan.target_id

    def _all_tasks(self, plan: LearningPlan) -> list[LearningPlanTask]:
        _days, by_day = self._load_days(plan)
        return [t for tasks in by_day.values() for t in tasks]
