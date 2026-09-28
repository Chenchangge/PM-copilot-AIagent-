"""分类体系初始配置（idempotent seed）。

职责：
- seed_taxonomy：落 ProductDirection / Specialization / KnowledgeCategory /
  KnowledgeTopic / Tag / InterviewType 及方向关联（缺失才插入，已存在跳过）。
- seed_question_knowledge：从 interview/data/questions.json 派生
  QuestionKnowledge（core / related / prerequisite）关系。

不批量创建知识点正文（当前 45 个 MVP 知识点以 Markdown 为 source of truth）。
"""
from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT
from app.learning.constants import (
    DIRECTIONS,
    INTERVIEW_TYPES,
    KNOWLEDGE_CATEGORIES,
    KNOWLEDGE_TOPICS,
    RELATION_CORE,
    RELATION_PREREQUISITE,
    RELATION_RELATED,
    SPECIALIZATIONS,
)
from app.models.taxonomy import (
    DirectionInterviewType,
    DirectionKnowledge,
    InterviewType,
    KnowledgeCategory,
    KnowledgeTopic,
    ProductDirection,
    QuestionKnowledge,
    Specialization,
    Tag,
)

QUESTIONS_FILE = PROJECT_ROOT / "interview" / "data" / "questions.json"

# 方向 → 分类权重（§14 示例：AI产品经理对 AI产品/产品基础高权重、数据分析中权重、商业化中低）。
# 未列出的 (direction, category) 组合默认 weight=1.0。
DIRECTION_CATEGORY_WEIGHTS = {
    ("AI产品经理", "ai-product"): 1.0,
    ("AI产品经理", "product-foundation"): 1.0,
    ("AI产品经理", "data-analysis"): 0.6,
    ("AI产品经理", "commercialization"): 0.4,
    ("数据产品经理", "data-analysis"): 1.0,
    ("数据产品经理", "product-foundation"): 0.8,
    ("C端产品经理", "product-foundation"): 1.0,
    ("C端产品经理", "user-growth"): 0.9,
    ("C端产品经理", "product-design"): 0.8,
    ("B端产品经理", "b2b-enterprise"): 1.0,
    ("B端产品经理", "product-foundation"): 0.9,
    ("B端产品经理", "project-collaboration"): 0.8,
}

# 方向 → 面试类型优先级（§15 初始配置；未列出的组合默认 priority=1）。
DIRECTION_INTERVIEW_PRIORITY = {
    ("AI产品经理", "AI产品"): 1,
    ("AI产品经理", "产品设计"): 2,
    ("AI产品经理", "数据分析"): 3,
    ("数据产品经理", "数据分析"): 1,
    ("数据产品经理", "产品设计"): 2,
    ("数据产品经理", "商业化与增长"): 3,
    ("C端产品经理", "用户研究"): 1,
    ("C端产品经理", "需求分析"): 2,
    ("C端产品经理", "商业化与增长"): 3,
}

# 工具统一作为 Tag（§一：Figma/Axure/SQL/Excel/XMind）
TOOL_TAGS = ["Figma", "Axure", "SQL", "Excel", "XMind"]

# 面试题 → 额外知识点关系（knowledge_ids 已作为 core；这里只补 related / prerequisite）
QUESTION_EXTRA_KNOWLEDGE = {
    "ai-rag-001": {"prerequisite": ["llm"]},
    "ai-embedding-001": {"prerequisite": ["llm"]},
    "ai-agent-001": {"prerequisite": ["llm"], "related": ["prompt-engineering"]},
    "ai-hallucination-001": {"related": ["rag"]},
}

# 旧 Specialization 命名重映射（行业解决方案 → 行业/解决方案），用于清理历史遗留行
_LEGACY_SPECIALIZATIONS = ["行业解决方案"]


def seed_taxonomy(db: Session) -> None:
    """幂等写入分类体系种子数据。"""
    _seed_simple(db, ProductDirection, [(d, d) for d in DIRECTIONS])
    _seed_simple(db, Specialization, [(s, s) for s in SPECIALIZATIONS])
    _seed_simple(db, KnowledgeCategory, KNOWLEDGE_CATEGORIES)
    _seed_simple(db, InterviewType, [(t, t) for t in INTERVIEW_TYPES])

    # Specialization 重命名清理：删除旧命名，避免与「行业/解决方案」并存重复
    for old in _LEGACY_SPECIALIZATIONS:
        _delete_by_id(db, Specialization, old)

    # KnowledgeTopic：三级结构 Category → Topic → Point
    # 清理旧 seed 的 1:1 遗留 topic（id == category_id，MVP 阶段 topic==category）
    for stale in db.execute(
        select(KnowledgeTopic).where(KnowledgeTopic.id == KnowledgeTopic.category_id)
    ).scalars().all():
        db.delete(stale)
    for category_slug, topic_slug, topic_name in KNOWLEDGE_TOPICS:
        _insert_if_missing(
            db, KnowledgeTopic, id=topic_slug, category_id=category_slug, name=topic_name
        )

    # 工具作为 Tag
    for tag_name in TOOL_TAGS:
        _insert_if_missing(db, Tag, id=tag_name, name=tag_name)

    # 方向 ↔ 分类（M:N + weight）
    for d in DIRECTIONS:
        for slug, _name in KNOWLEDGE_CATEGORIES:
            weight = DIRECTION_CATEGORY_WEIGHTS.get((d, slug), 1.0)
            _insert_if_missing(
                db, DirectionKnowledge, direction_id=d, category_id=slug, weight=weight, priority=1
            )

    # 方向 ↔ 面试类型（M:N）
    for d in DIRECTIONS:
        for t in INTERVIEW_TYPES:
            priority = DIRECTION_INTERVIEW_PRIORITY.get((d, t), 5)
            _insert_if_missing(
                db, DirectionInterviewType, direction_id=d, interview_type_id=t, priority=priority
            )

    db.commit()


def seed_question_knowledge(db: Session) -> None:
    """从 questions.json 派生 QuestionKnowledge 关系（幂等）。

    - 每个题目的 knowledge_ids 记为 core；
    - knowledge_relations 补充 related / prerequisite（若题目带该字段）；
    - QUESTION_EXTRA_KNOWLEDGE 作为旧题库的兜底补充（无 knowledge_relations 时）。
    """
    questions = _load_questions()
    for q in questions:
        qid = q["id"]
        for kid in q.get("knowledge_ids", []):
            _insert_question_knowledge(db, qid, kid, RELATION_CORE)
        rels = q.get("knowledge_relations")
        if rels:
            for rel in rels:
                rt = rel.get("relation_type")
                kid = rel.get("point_id")
                if not kid:
                    continue
                if rt == RELATION_RELATED:
                    _insert_question_knowledge(db, qid, kid, RELATION_RELATED)
                elif rt == RELATION_PREREQUISITE:
                    _insert_question_knowledge(db, qid, kid, RELATION_PREREQUISITE)
        else:
            extra = QUESTION_EXTRA_KNOWLEDGE.get(qid, {})
            for kid in extra.get("prerequisite", []):
                _insert_question_knowledge(db, qid, kid, RELATION_PREREQUISITE)
            for kid in extra.get("related", []):
                _insert_question_knowledge(db, qid, kid, RELATION_RELATED)
    db.commit()


def _load_questions() -> list[dict]:
    if not QUESTIONS_FILE.exists():
        return []
    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _insert_question_knowledge(db: Session, question_id: str, knowledge_point_id: str, relation_type: str) -> None:
    exists = db.execute(
        select(QuestionKnowledge).where(
            QuestionKnowledge.question_id == question_id,
            QuestionKnowledge.knowledge_point_id == knowledge_point_id,
            QuestionKnowledge.relation_type == relation_type,
        )
    ).scalars().first()
    if exists is None:
        db.add(
            QuestionKnowledge(
                question_id=question_id,
                knowledge_point_id=knowledge_point_id,
                relation_type=relation_type,
            )
        )


def _seed_simple(db: Session, model, items: list[tuple[str, str]]) -> None:
    for id_, name in items:
        _insert_if_missing(db, model, id=id_, name=name)


def _insert_if_missing(db: Session, model, **kwargs) -> None:
    ident = kwargs.get("id")
    if ident is None:
        return
    exists = db.execute(select(model).where(model.id == ident)).scalars().first()
    if exists is None:
        db.add(model(**kwargs))


def _delete_by_id(db: Session, model, ident: str) -> None:
    row = db.execute(select(model).where(model.id == ident)).scalars().first()
    if row is not None:
        db.delete(row)
