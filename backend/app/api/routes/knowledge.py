"""知识库 Learning 路由（Step 10-2，真实 Markdown 数据源）。

Route 保持薄层：HTTP → KnowledgeService → HTTP。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.routes.models import get_user_id
from app.db.database import get_db
from app.schemas.knowledge import KnowledgeDetail, KnowledgeListResponse
from app.services.knowledge_index_service import rebuild_knowledge_index
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.get("", response_model=KnowledgeListResponse)
def list_knowledge(
    category: str | None = Query(default=None),
    topic: str | None = Query(default=None),
) -> KnowledgeListResponse:
    return KnowledgeService().list_knowledge(category, topic)


@router.post("/reindex")
def reindex_knowledge(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict:
    return rebuild_knowledge_index(db, user_id)


@router.get("/{knowledge_id}", response_model=KnowledgeDetail)
def get_knowledge(
    knowledge_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> KnowledgeDetail:
    return KnowledgeService(db=db, user_id=user_id).get_knowledge(knowledge_id)
