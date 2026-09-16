"""用户相关路由（占位）。"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_profile() -> dict:
    # TODO: 返回用户信息
    return {"name": "PM", "level": "入门"}


@router.get("/learning-history")
def learning_history() -> dict:
    # TODO: 返回学习记录
    return {"items": []}


@router.get("/interview-history")
def interview_history() -> dict:
    # TODO: 返回面试记录
    return {"items": []}
