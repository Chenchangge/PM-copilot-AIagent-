"""模拟面试 API 的请求 / 响应 Schema。"""
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.interview.constants import DIFFICULTIES, DIRECTIONS, INTERVIEW_TYPES


class CreateSessionRequest(BaseModel):
    direction: str
    difficulty: str
    interview_type: str

    @field_validator("direction")
    @classmethod
    def _check_direction(cls, v: str) -> str:
        if v not in DIRECTIONS:
            raise ValueError(f"非法的面试方向：{v}")
        return v

    @field_validator("difficulty")
    @classmethod
    def _check_difficulty(cls, v: str) -> str:
        if v not in DIFFICULTIES:
            raise ValueError(f"非法的难度：{v}")
        return v

    @field_validator("interview_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in INTERVIEW_TYPES:
            raise ValueError(f"非法的面试类型：{v}")
        return v


class SubmitAnswerRequest(BaseModel):
    answer: str
    client_request_id: str | None = None


class QuestionOut(BaseModel):
    turn_id: int
    content: str
    type: str  # main | follow_up
    round: int
    follow_up_type: str | None = None


class SessionOut(BaseModel):
    id: str
    status: str
    direction: str
    difficulty: str
    interview_type: str
    current_round: int
    max_main_questions: int = 5
    end_reason: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class TurnOut(BaseModel):
    turn_id: int
    round: int
    type: str  # main | follow_up
    question_id: str | None = None
    question_content: str
    follow_up_type: str | None = None
    answer_content: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
    current_round: int
    question: QuestionOut


class AnswerResponse(BaseModel):
    session_id: str
    status: str
    current_round: int
    action: str  # follow_up | next_question | completed
    question: QuestionOut | None = None


class SessionDetailResponse(BaseModel):
    session: SessionOut
    current_question: QuestionOut | None = None
    turns: list[TurnOut]
