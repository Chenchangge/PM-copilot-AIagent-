"""学习计划相关路由（Step 12-3 Part B）。

Route 保持薄层：HTTP → LearningService → HTTP。
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.models import get_user_id
from app.db.database import get_db
from app.learning.constants import (
    CURRENT_LEVELS,
    DAILY_MINUTES_OPTIONS,
    INTENSITIES,
)
from app.learning.service import LearningService
from app.schemas.learning import (
    CreatePlanRequest,
    EstimateRequest,
    EstimateResult,
    HomeSummaryOut,
    PlanDetailOut,
    PlanListResponse,
    PlanTaxonomyOut,
    TaxonomyOut,
    TaskOut,
    UpdatePlanRequest,
)

router = APIRouter()


@router.get("/taxonomy", response_model=None)
def get_taxonomy(
    scope: Literal["default", "plan"] = "default",
    current_level: str = "基础",
    daily_minutes: int = 30,
    intensity: str = "标准",
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> TaxonomyOut | PlanTaxonomyOut:
    """分类体系。

    - 不带 scope：保持旧行为（11 分类 / 22 专题 / 全量 tags），兼容知识库页；
    - scope=plan：学习计划页专用精简结构，不返回 640 个 tags。
    """
    if scope == "default":
        return LearningService(db).get_taxonomy()

    if current_level not in CURRENT_LEVELS:
        raise HTTPException(status_code=422, detail=f"非法的当前水平：{current_level}")
    if daily_minutes not in DAILY_MINUTES_OPTIONS:
        raise HTTPException(status_code=422, detail=f"非法的每日学习时间：{daily_minutes}")
    if intensity not in INTENSITIES:
        raise HTTPException(status_code=422, detail=f"非法的学习强度：{intensity}")
    return LearningService(db).get_plan_taxonomy(user_id, current_level, daily_minutes, intensity)


@router.get("/home-summary", response_model=HomeSummaryOut)
def home_summary(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> HomeSummaryOut:
    return LearningService(db).home_summary(user_id)


@router.post("/plans/estimate", response_model=EstimateResult)
def estimate(
    payload: EstimateRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> EstimateResult:
    return LearningService(db).estimate(user_id, payload)


@router.post("/plans", response_model=PlanDetailOut, status_code=201)
def create_plan(
    payload: CreatePlanRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> PlanDetailOut:
    return LearningService(db).create_plan(user_id, payload)


@router.get("/plans", response_model=PlanListResponse)
def list_plans(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> PlanListResponse:
    return LearningService(db).list_plans(user_id)


@router.get("/plans/{plan_id}", response_model=PlanDetailOut)
def get_plan(plan_id: int, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> PlanDetailOut:
    return LearningService(db).get_plan(user_id, plan_id)


@router.post("/plans/{plan_id}/pause", response_model=PlanDetailOut)
def pause_plan(plan_id: int, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> PlanDetailOut:
    return LearningService(db).pause(user_id, plan_id)


@router.post("/plans/{plan_id}/resume", response_model=PlanDetailOut)
def resume_plan(plan_id: int, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> PlanDetailOut:
    return LearningService(db).resume(user_id, plan_id)


@router.patch("/plans/{plan_id}", response_model=PlanDetailOut)
def update_plan(
    plan_id: int,
    payload: UpdatePlanRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> PlanDetailOut:
    return LearningService(db).update_plan(user_id, plan_id, payload)


@router.post("/tasks/{task_id}/start", response_model=TaskOut)
def start_task(task_id: int, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> TaskOut:
    return LearningService(db).start_task(user_id, task_id)


@router.post("/tasks/{task_id}/complete", response_model=PlanDetailOut)
def complete_task(task_id: int, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> PlanDetailOut:
    return LearningService(db).complete_task(user_id, task_id)


@router.post("/knowledge/{knowledge_id}/start")
def start_knowledge(knowledge_id: str, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> dict:
    return LearningService(db).start_knowledge(user_id, knowledge_id)


@router.post("/knowledge/{knowledge_id}/complete")
def complete_knowledge(knowledge_id: str, user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> dict:
    return LearningService(db).complete_knowledge(user_id, knowledge_id)
