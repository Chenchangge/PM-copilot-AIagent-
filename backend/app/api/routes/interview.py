"""模拟面试相关路由（Step 8-2 / 9-2）。

Route 保持薄层：HTTP → InterviewService / EvaluationService → HTTP。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.models import get_user_id
from app.db.database import get_db
from app.schemas.evaluation import EvaluationReport
from app.schemas.interview import (
    AnswerResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionDetailResponse,
    SessionOut,
    SubmitAnswerRequest,
)
from app.services.evaluation_service import EvaluationService
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
def create_session(
    payload: CreateSessionRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> CreateSessionResponse:
    return InterviewService(db).create_session(
        user_id, payload.direction, payload.difficulty, payload.interview_type
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    return InterviewService(db).get_session(user_id, session_id)


@router.post("/sessions/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: str,
    payload: SubmitAnswerRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> AnswerResponse:
    return InterviewService(db).submit_answer(
        user_id, session_id, payload.answer, payload.client_request_id
    )


@router.post("/sessions/{session_id}/finish", response_model=SessionOut)
def finish_session(
    session_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> SessionOut:
    return InterviewService(db).finish(user_id, session_id)


@router.post("/sessions/{session_id}/evaluation", response_model=EvaluationReport)
def trigger_evaluation(
    session_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> EvaluationReport:
    return EvaluationService(db).evaluate_session(user_id, session_id)


@router.get("/sessions/{session_id}/evaluation")
def get_evaluation(
    session_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    # completed → EvaluationReport；failed → {session_id, status, error}
    return EvaluationService(db).get_evaluation(user_id, session_id)
