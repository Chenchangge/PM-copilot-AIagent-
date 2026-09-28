"""Learning Plan 的知识点索引：Markdown → KnowledgePointView（含最小兼容回退）。

数据源原则：当前 45 个 MVP 知识点仍以 Markdown 为 source of truth。本模块只做
「读取 + 回退填充」，不批量修改 Markdown、不重新分类、不落 knowledge_points 表。

回退规则（§40 最小兼容）：
- difficulty：legacy beginner/intermediate/advanced → 入门/进阶/高级
- estimated_minutes：缺失时按 difficulty + content 长度保守回退（source=fallback）
- quality_status：legacy 内容默认 reviewed（可被 Learning Plan 推荐）
- topic：legacy 数据无独立 topic，默认等于 category（KnowledgeTopic 实体已就绪，
  未来 ingestion 写入更细 topic）
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.learning.constants import (
    ALLOWED_MINUTES,
    DIFFICULTY_MINUTES,
    DIRECTION_CATEGORIES,
    LONG_CONTENT_BONUS_MINUTES,
    LONG_CONTENT_CHARS,
    MINUTES_SOURCE_FALLBACK,
    MINUTES_SOURCE_MANUAL,
    QUALITY_REVIEWED,
    TARGET_TYPE_CATEGORY,
    TARGET_TYPE_DIRECTION,
    TARGET_TYPE_TAG,
    TARGET_TYPE_TOPIC,
)
from app.rag.document import KnowledgeDocument
from app.rag.loader import MarkdownLoader

_LEGACY_DIFFICULTY_MAP = {
    "beginner": "入门",
    "intermediate": "进阶",
    "advanced": "高级",
}


@dataclass
class KnowledgePointView:
    """Learning Plan 视角下的知识点（兼容视图，非 DB 实体）。"""

    id: str
    title: str
    category: str  # legacy slug，如 ai
    topic: str = ""  # legacy 阶段 == category
    tags: list[str] = field(default_factory=list)
    difficulty: str = "入门"
    estimated_minutes: int = 15
    estimated_minutes_source: str = MINUTES_SOURCE_FALLBACK
    quality_status: str = QUALITY_REVIEWED
    dependencies: list[str] = field(default_factory=list)
    summary: str = ""
    source_path: str = ""


def _map_difficulty(legacy: str) -> str:
    return _LEGACY_DIFFICULTY_MAP.get(legacy, legacy or "入门")


def _snap_minutes(value: int) -> int:
    """把分钟数收敛到允许值 [5,10,15,20,30,45,60]。"""
    return min(ALLOWED_MINUTES, key=lambda x: abs(x - value))


def fallback_minutes(difficulty: str, content_length: int) -> int:
    """缺失 estimated_minutes 时的保守回退：difficulty + content 长度。"""
    base = DIFFICULTY_MINUTES.get(difficulty, 15)
    if content_length > LONG_CONTENT_CHARS:
        base += LONG_CONTENT_BONUS_MINUTES
    return _snap_minutes(base)


def _to_view(doc: KnowledgeDocument) -> KnowledgePointView:
    difficulty = _map_difficulty(doc.difficulty)
    content_length = len(doc.content)

    if doc.estimated_minutes is not None and doc.estimated_minutes > 0:
        estimated_minutes = _snap_minutes(doc.estimated_minutes)
        source = MINUTES_SOURCE_MANUAL
    else:
        estimated_minutes = fallback_minutes(difficulty, content_length)
        source = MINUTES_SOURCE_FALLBACK

    topic = doc.topic or doc.category

    # summary 用正文首段做轻量摘要（仅用于展示，非正式 summary 字段）
    first_line = ""
    for line in doc.content.splitlines():
        stripped = line.strip()
        if stripped:
            first_line = stripped
            break

    return KnowledgePointView(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        topic=topic,
        tags=list(doc.tags),
        difficulty=difficulty,
        estimated_minutes=estimated_minutes,
        estimated_minutes_source=source,
        quality_status=QUALITY_REVIEWED,
        dependencies=list(doc.dependencies),
        summary=first_line,
        source_path=doc.source_path,
    )


def build_knowledge_index(loader: MarkdownLoader | None = None) -> dict[str, KnowledgePointView]:
    """knowledge_id → KnowledgePointView。"""
    docs = (loader or MarkdownLoader()).load()
    return {d.id: _to_view(d) for d in docs}


def build_knowledge_list(loader: MarkdownLoader | None = None) -> list[KnowledgePointView]:
    """按加载顺序返回知识点视图列表。"""
    docs = (loader or MarkdownLoader()).load()
    return [_to_view(d) for d in docs]


def resolve_target(
    index: dict[str, KnowledgePointView], target_type: str, target_id: str
) -> list[KnowledgePointView]:
    """按目标类型解析知识点范围（§18 / §十一）。

    - category：最终 taxonomy 一级分类 slug（如 ai-product）
    - topic：二级主题 slug（如 rag-retrieval）
    - tag：知识点 tag 名（如 SQL / RAG）
    - direction：产品方向（如 AI产品经理）→ 相关一级分类 → 知识点
    """
    out: list[KnowledgePointView] = []
    direction_cats = DIRECTION_CATEGORIES.get(target_id, []) if target_type == TARGET_TYPE_DIRECTION else []
    for p in index.values():
        if target_type == TARGET_TYPE_CATEGORY and p.category == target_id:
            out.append(p)
        elif target_type == TARGET_TYPE_TOPIC and (p.topic or p.category) == target_id:
            out.append(p)
        elif target_type == TARGET_TYPE_TAG and target_id in p.tags:
            out.append(p)
        elif target_type == TARGET_TYPE_DIRECTION and p.category in direction_cats:
            out.append(p)
    return out
