"""用户相关路由（学习记录 / 面试记录 / 资料占位）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.routes.models import get_user_id
from app.db.database import get_db
from app.schemas.profile import InterviewHistoryResponse, LearningHistoryResponse
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/")
def get_profile() -> dict:
    return {"name": "PM", "level": "入门"}


@router.get("/learning-history", response_model=LearningHistoryResponse)
def learning_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> LearningHistoryResponse:
    return ProfileService(db).learning_history(user_id, page, page_size)


@router.get("/interview-history", response_model=InterviewHistoryResponse)
def interview_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> InterviewHistoryResponse:
    return ProfileService(db).interview_history(user_id, page, page_size)
