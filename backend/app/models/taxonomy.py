"""分类体系（Taxonomy）数据模型（Step 12-3 Part A）。

把已确定的产品分类 / 知识分类 / 面试分类及其关联关系落入数据模型：
- ProductDirection / Specialization / KnowledgeCategory / KnowledgeTopic / Tag / InterviewType
- 关联：DirectionKnowledge（方向↔分类，带 weight/priority）、DirectionInterviewType（方向↔面试类型）
- KnowledgePoint 最终模型（未来 ingestion 写入；MVP 阶段以 Markdown 为数据源）
- M:N：KnowledgePointTag、KnowledgePointDependency（硬前置）、KnowledgePointRelated（related/similar/...）
- QuestionKnowledge（题目↔知识点，relation_type = core/related/prerequisite）

这些表是「正式模型 + 初始配置」，不批量落当前 45 个 MVP 知识点。
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ProductDirection(Base):
    __tablename__ = "product_directions"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # 中文名，如「AI产品经理」
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Specialization(Base):
    __tablename__ = "specializations"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # 中文名，如「策略」
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug，如 ai-product
    name: Mapped[str] = mapped_column(String, nullable=False)   # 中文名，如 AI产品
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class KnowledgeTopic(Base):
    __tablename__ = "knowledge_topics"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug
    category_id: Mapped[str] = mapped_column(String, nullable=False)  # 所属分类 slug
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class InterviewType(Base):
    __tablename__ = "interview_types"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # 中文名
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DirectionKnowledge(Base):
    """ProductDirection ↔ KnowledgeCategory M:N，带 weight/priority（方向对分类的重要程度）。"""

    __tablename__ = "direction_knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    direction_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    category_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DirectionInterviewType(Base):
    """ProductDirection ↔ InterviewType M:N（不同方向选择不同面试题类型）。"""

    __tablename__ = "direction_interview_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    direction_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    interview_type_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class KnowledgePoint(Base):
    """知识点最终模型（Step 12-2-2 §8）。

    MVP 阶段以 Markdown 为数据源，本表为未来 ingestion 的目标 schema；
    primary_category 只能有一个，secondary_topic 只能有一个，tags 可多个。
    """

    __tablename__ = "knowledge_points"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug
    title: Mapped[str] = mapped_column(String, nullable=False)
    primary_category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    secondary_topic_id: Mapped[str | None] = mapped_column(String, nullable=True)
    difficulty: Mapped[str] = mapped_column(String, nullable=False, default="基础")
    summary: Mapped[str] = mapped_column(String, nullable=False, default="")
    definition: Mapped[str] = mapped_column(String, nullable=False, default="")
    core_content: Mapped[str] = mapped_column(String, nullable=False, default="")
    scenarios: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    pm_focus: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    common_misconceptions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cases: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dependencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    related_knowledge: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    quality_status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class KnowledgePointTag(Base):
    """KnowledgePoint ↔ Tag M:N。"""

    __tablename__ = "knowledge_point_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_point_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    tag_id: Mapped[str] = mapped_column(String, index=True, nullable=False)


class KnowledgePointDependency(Base):
    """知识点硬前置依赖（AND，有方向）。"""

    __tablename__ = "knowledge_point_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_point_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    depends_on_id: Mapped[str] = mapped_column(String, index=True, nullable=False)


class KnowledgePointRelated(Base):
    """知识点非前置关联（related/similar/supersedes/deprecated_by），不影响排课。"""

    __tablename__ = "knowledge_point_related"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_point_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    related_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    relation_type: Mapped[str] = mapped_column(String, nullable=False, default="related")


class QuestionKnowledge(Base):
    """面试题 ↔ 知识点（relation_type = core/related/prerequisite）。

    question_id 对应 interview/data/questions.json 中的题目 id；保持 Interview Engine 兼容。
    """

    __tablename__ = "question_knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    knowledge_point_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    relation_type: Mapped[str] = mapped_column(String, nullable=False, default="core")
