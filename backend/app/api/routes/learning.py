"""学习计划相关路由（Step 12-3 Part B）。

Route 保持薄层：HTTP → LearningService → HTTP。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.models import get_user_id
from app.db.database import get_db
from app.learning.service import LearningService
from app.schemas.learning import (
    CreatePlanRequest,
    EstimateRequest,
    EstimateResult,
    HomeSummaryOut,
    PlanDetailOut,
    PlanListResponse,
    TaxonomyOut,
    TaskOut,
    UpdatePlanRequest,
)

router = APIRouter()


@router.get("/taxonomy", response_model=TaxonomyOut)
def get_taxonomy(db: Session = Depends(get_db)) -> TaxonomyOut:
    return LearningService(db).get_taxonomy()


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
