"""知识库相关路由（占位，未接入 RAG）。"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_knowledge() -> dict:
    # TODO: 从 RAG 知识库检索，当前返回占位数据
    return {"items": []}


@router.get("/{knowledge_id}")
def get_knowledge(knowledge_id: int) -> dict:
    # TODO: 返回单条知识详情
    return {"id": knowledge_id, "title": "占位", "content": ""}
