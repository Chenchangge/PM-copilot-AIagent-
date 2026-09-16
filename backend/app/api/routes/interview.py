"""模拟面试相关路由（占位，未接入 AI）。"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/sessions")
def create_session() -> dict:
    # TODO: 创建模拟面试会话（调用 DeepSeek 生成题目）
    return {"id": "mock-session", "status": "created"}


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    # TODO: 返回会话详情
    return {"id": session_id}


@router.post("/sessions/{session_id}/report")
def generate_report(session_id: str) -> dict:
    # TODO: 调用评价服务生成报告
    return {"id": session_id, "report": {}}
