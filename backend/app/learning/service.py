"""Learning Plan 核心服务（Step 12-3 Part B）。

职责边界（§33）：
- Backend（确定性）：目标范围解析、draft/deprecated 过滤、依赖拓扑排序、学习量计算、
  日期排课、进度计算、完成状态计算。
- AI（可选、非单点故障）：学习周期解释 / 学习重点 / 学习建议；AI 不可用时回退确定性文案。

进度一致性（§35）：progress 一律由后端按 task 状态重算，前端只提交 task 完成。
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.learning.constants import (
    CATEGORY_INTERVIEW_TYPES,
    CATEGORY_NAMES,
    CURRENT_LEVELS,
    DAILY_MINUTES_OPTIONS,
    DAY_CHOICES,
    DIRECTION_CATEGORIES,
    DIRECTIONS,
    INTENSITIES,
    INTERVIEW_RECOMMEND_RATIO,
    KNOWLEDGE_CATEGORIES,
    KNOWLEDGE_TOPICS,
    LEGACY_CATEGORY_LABELS,
    PLAN_ACTIVE,
    PLAN_COMPLETED,
    PLAN_PAUSED,
    RECORD_COMPLETED,
    RECORD_STARTED,
    TARGET_TYPE_CATEGORY,
    TARGET_TYPE_DIRECTION,
    TARGET_TYPE_TAG,
    TARGET_TYPE_TOPIC,
    TASK_COMPLETED,
    TASK_IN_PROGRESS,
    TASK_PENDING,
    TOPIC_CATEGORY,
    TOPIC_NAMES,
)
from app.learning.errors import LearningError, LearningErrorCode
from app.learning.knowledge_index import KnowledgePointView, build_knowledge_index, resolve_target
from app.learning.planner import (
    compute_recommended_days,
    compute_total_minutes,
    distribute,
    filter_recommendable,
    schedule_points,
)
from app.models.learning import KnowledgeLearningRecord, LearningPlan, LearningPlanDay, LearningPlanTask
from app.schemas.learning import (
    CategoryOut,
    CreatePlanRequest,
    DayOut,
    EstimateRequest,
    EstimateResult,
    HomeSummaryOut,
    PlanDetailOut,
    PlanListItem,
    PlanListResponse,
    PrerequisiteInfo,
    RecommendedInterview,
    TargetInfo,
    TaskOut,
    TaxonomyOut,
    TodayProgress,
    TopicOut,
    UpdatePlanRequest,
)

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
        """返回最终 taxonomy（11 分类 → 18 二级主题 → Tag），供学习计划目标选择。"""
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

    # ================= estimate =================
    def estimate(self, user_id: str, req: EstimateRequest) -> EstimateResult:
        ordered, target_name = self._resolve_ordered(req)
        total_minutes = compute_total_minutes(ordered)
        recommended_days = compute_recommended_days(total_minutes, req.daily_minutes)

        key_topics = [p.title for p in ordered[:6]]
        explanation = self._ai_explain(
            user_id,
            {
                "target_name": target_name,
                "knowledge_count": len(ordered),
                "total_minutes": total_minutes,
                "daily_minutes": req.daily_minutes,
                "recommended_days": recommended_days,
                "current_level": req.current_level,
                "direction": req.direction_id,
                "key_topics": key_topics,
            },
        )
        day_choices = sorted(set([recommended_days] + list(DAY_CHOICES)))

        return EstimateResult(
            target=TargetInfo(type=req.target_type, id=req.target_id, name=target_name),
            knowledge_count=len(ordered),
            total_minutes=total_minutes,
            recommended_days=recommended_days,
            recommended_daily_minutes=req.daily_minutes,
            key_topics=key_topics,
            prerequisites=self._prerequisites(ordered),
            explanation=explanation,
            day_choices=day_choices,
        )

    # ================= 创建 / 查询计划 =================
    def create_plan(self, user_id: str, req: CreatePlanRequest) -> PlanDetailOut:
        ordered, target_name = self._resolve_ordered(req)
        total_minutes = compute_total_minutes(ordered)
        recommended_days = compute_recommended_days(total_minutes, req.daily_minutes)
        selected_days = req.selected_days if req.selected_days > 0 else recommended_days

        days = distribute(ordered, req.daily_minutes, selected_days)

        plan = LearningPlan(
            user_id=user_id,
            title=req.title or self._default_title(req.target_type, target_name, req.direction_id),
            target_type=req.target_type,
            target_id=req.target_id,
            target_name=target_name,
            direction_id=req.direction_id,
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
        self._reschedule_remaining(plan, new_daily, new_days)
        self._recompute_plan(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

    # ================= 任务 =================
    def start_task(self, user_id: str, task_id: int) -> TaskOut:
        task, plan = self._get_task(user_id, task_id)
        if task.status == TASK_COMPLETED:
            raise LearningError(LearningErrorCode.learning_task_state, "任务已完成")
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
        if task.status == "skipped":
            raise LearningError(LearningErrorCode.learning_task_state, "已跳过的任务无法完成")
        task.status = TASK_COMPLETED
        task.completed_at = _utcnow()
        self._complete_record(user_id, plan, task)
        self._recompute_plan(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_detail(plan)

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
        done = sum(1 for t in today_tasks if t.status == TASK_COMPLETED)
        minutes = sum(t.estimated_minutes for t in today_tasks if t.status == TASK_COMPLETED)

        next_action = "continue"
        if plan.status == PLAN_COMPLETED:
            next_action = "interview"
        elif today_tasks and done == len(today_tasks):
            next_action = "day_done"

        return HomeSummaryOut(
            active_plan=self._plan_item(plan),
            today_tasks=[self._task_out(t) for t in today_tasks],
            overall_progress=plan.progress_percent,
            today_progress=TodayProgress(done=done, total=len(today_tasks), minutes=minutes),
            recommended_next_action=next_action,
        )

    # ================= 内部：目标解析 =================
    def _resolve_ordered(self, req) -> tuple[list[KnowledgePointView], str]:
        target_name = self._target_name(req.target_type, req.target_id)
        points = filter_recommendable(resolve_target(self.index, req.target_type, req.target_id))
        if not points:
            raise LearningError(
                LearningErrorCode.learning_target_empty,
                f"该目标下没有可学习的内容：{target_name}",
            )
        return schedule_points(points), target_name

    def _target_name(self, target_type: str, target_id: str) -> str:
        if target_type == TARGET_TYPE_TAG:
            return target_id
        if target_type == TARGET_TYPE_DIRECTION:
            return target_id  # 方向中文名即目标名
        if target_type == TARGET_TYPE_TOPIC:
            return TOPIC_NAMES.get(target_id, LEGACY_CATEGORY_LABELS.get(target_id, target_id))
        return CATEGORY_NAMES.get(target_id, LEGACY_CATEGORY_LABELS.get(target_id, target_id))

    def _default_title(self, target_type: str, target_name: str, direction: str | None) -> str:
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
            f"目标「{ctx['target_name']}」共 {ctx['knowledge_count']} 个知识点、约 "
            f"{ctx['total_minutes']} 分钟。按每天 {ctx['daily_minutes']} 分钟，建议 "
            f"{ctx['recommended_days']} 天完成。学习重点：{'、'.join(ctx['key_topics']) or '无'}。"
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
            if t.status != TASK_COMPLETED
        ]
        pending_points = schedule_points([p for p in pending_points if p is not None])

        # 删除未完成任务（已完成任务冻结在原 Day）
        for t in all_tasks:
            if t.status != TASK_COMPLETED:
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

        plan.total_knowledge_points = len(all_tasks)
        plan.total_estimated_minutes = sum(t.estimated_minutes for t in all_tasks)
        completed = [t for t in all_tasks if t.status == TASK_COMPLETED]
        plan.completed_knowledge_points = len(completed)
        plan.completed_minutes = sum(t.estimated_minutes for t in completed)
        plan.progress_percent = round(len(completed) / len(all_tasks) * 100) if all_tasks else 0
        if all_tasks and len(completed) == len(all_tasks):
            plan.status = PLAN_COMPLETED
            plan.completed_at = plan.completed_at or _utcnow()

        days_by_id = {d.id: d for d in days}
        for day_id, tasks in tasks_by_day.items():
            day = days_by_id[day_id]
            planned = sum(t.estimated_minutes for t in tasks)
            done = sum(t.estimated_minutes for t in tasks if t.status == TASK_COMPLETED)
            day.planned_minutes = planned
            day.completed_minutes = done
            day.progress_percent = round(done / planned * 100) if planned else 0
            if tasks and all(t.status == TASK_COMPLETED for t in tasks):
                day.status = "completed"
                day.completed_at = day.completed_at or _utcnow()
            elif any(t.status in (TASK_COMPLETED, TASK_IN_PROGRESS) for t in tasks):
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
            if d.status != "completed":
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
            title=doc.title if doc else t.knowledge_point_id,
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
