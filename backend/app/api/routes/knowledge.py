"""知识库 Learning 路由（Step 10-2，真实 Markdown 数据源）。

Route 保持薄层：HTTP → KnowledgeService → HTTP。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.knowledge import KnowledgeDetail, KnowledgeListResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.get("", response_model=KnowledgeListResponse)
def list_knowledge(
    category: str | None = Query(default=None),
    topic: str | None = Query(default=None),
) -> KnowledgeListResponse:
    return KnowledgeService().list_knowledge(category, topic)


@router.get("/{knowledge_id}", response_model=KnowledgeDetail)
def get_knowledge(knowledge_id: str, db: Session = Depends(get_db)) -> KnowledgeDetail:
    return KnowledgeService(db=db).get_knowledge(knowledge_id)
