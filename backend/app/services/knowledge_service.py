"""知识库 Learning 服务：从 Markdown 加载并解析为结构化知识。

数据源原则（Step 10）：Markdown = Knowledge Source of Truth。本服务只读
`knowledge/data/*.md`，不新建 SQLite 表、不复制内容、不做 RAG。

复用 `MarkdownLoader`（front matter + H1 剥离），并在此做「## 章节 → 结构化字段」
的解析（章节标题来自审计结论，见 Step 10-1）。
"""
from __future__ import annotations

import re
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.interview.question_bank import QuestionBank
from app.models.learning import KnowledgeLearningRecord
from app.models.taxonomy import QuestionKnowledge
from app.rag.document import KnowledgeDocument
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.loader import MarkdownLoader
from app.schemas.knowledge import (
    KnowledgeDetail,
    KnowledgeInterviewQuestion,
    KnowledgeLink,
    KnowledgeListItem,
    KnowledgeListResponse,
    KnowledgeRelatedQuestion,
)

SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
SUB_RE = re.compile(r"^###\s*(.+)$", re.MULTILINE)

# 章节标题 → 详情字段（标题以 knowledge/data/*.md 实际为准）
S_DEFINITION = "定义"
S_CORE_CONTENT = "核心内容"
S_COMMON_SCENARIOS = "常见场景"
S_PM_FOCUS = "产品经理关注点"
S_INTERVIEW_QUESTIONS = "面试问题"
S_REFERENCE_ANSWERS = "参考答案"
S_MISCONCEPTIONS = "常见误区"
S_CASES = "案例"
MAX_RELATED_KNOWLEDGE = 5
MAX_RELATED_QUESTIONS = 5


@lru_cache(maxsize=1)
def _question_map() -> dict[str, dict]:
    """题库 id → 题目（详情页相关题的内容/难度/参考答案）。静态数据，进程内缓存。"""
    try:
        bank = QuestionBank()
        bank.load()
    except Exception:  # noqa: BLE001 - 题库缺失不应阻断知识详情
        return {}
    return {q["id"]: q for q in bank.all()}


def _split_sections(content: str) -> list[tuple[str, str]]:
    """按 `## ` 标题切分正文为 (标题, 文本)。与 chunker 逻辑等价，但不依赖其内部实现。"""
    matches = list(SECTION_RE.finditer(content))
    if not matches:
        return [("", content)]
    sections = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections.append((title, content[start:end]))
    return sections


def _parse_bullets(text: str) -> list[str]:
    """解析 `- item` / `* item` / `1. item` 列表为字符串数组。

    无列表项时，若正文非空则整段作为一项（兼容非列表格式，避免丢内容）。
    """
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = re.match(r"^[-*]\s+(.+)$", stripped)
        if m:
            items.append(m.group(1).strip())
        elif re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s*", "", stripped).strip())
    if items:
        return items
    text = text.strip()
    return [text] if text else []


def _parse_questions(text: str) -> list[dict]:
    """解析 `### 1. 问题` / `### 2. 问题` 为 [{question}]（去掉编号）。"""
    questions: list[dict] = []
    for m in SUB_RE.finditer(text):
        q = re.sub(r"^\d+\.\s*", "", m.group(1).strip()).strip()
        if q:
            questions.append({"question": q})
    return questions


def _parse_answers(text: str) -> list[dict]:
    """解析 `### 问题 N` + 正文 为 [{question, answer}]。"""
    matches = list(SUB_RE.finditer(text))
    if not matches:
        text = text.strip()
        return [{"question": "", "answer": text}] if text else []
    answers: list[dict] = []
    for i, m in enumerate(matches):
        label = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        answers.append({"question": label, "answer": text[start:end].strip()})
    return answers


def _question_links(question: dict, knowledge_id: str) -> bool:
    """题目是否关联某知识点（knowledge_ids 或 knowledge_relations 任一命中）。"""
    if knowledge_id in (question.get("knowledge_ids") or []):
        return True
    return any(
        rel.get("point_id") == knowledge_id
        for rel in (question.get("knowledge_relations") or [])
        if isinstance(rel, dict)
    )


def _merge_qa(questions: list[dict], answers: list[dict]) -> list[KnowledgeInterviewQuestion]:
    """按顺序合并面试问题与参考答案；数量不一致时尽量保留数据，不报错。"""
    merged: list[KnowledgeInterviewQuestion] = []
    n = max(len(questions), len(answers))
    for i in range(n):
        q = questions[i]["question"] if i < len(questions) else (answers[i]["question"] if i < len(answers) else "")
        a = answers[i]["answer"] if i < len(answers) else ""
        merged.append(KnowledgeInterviewQuestion(question=q, reference_answer=a))
    return merged


class KnowledgeService:
    def __init__(
        self,
        loader: MarkdownLoader | None = None,
        db: Session | None = None,
        user_id: str | None = None,
    ) -> None:
        self.loader = loader or MarkdownLoader()
        self.db = db
        self.user_id = user_id
        self._db_failed = False
        self._docs: list[KnowledgeDocument] | None = None
        self._docs_by_id: dict[str, KnowledgeDocument] | None = None

    def _load(self) -> list[KnowledgeDocument]:
        if self._docs is None:
            self._docs = self.loader.load()
        return self._docs

    def _by_id(self) -> dict[str, KnowledgeDocument]:
        if self._docs_by_id is None:
            self._docs_by_id = {d.id: d for d in self._load()}
        return self._docs_by_id

    def list_knowledge(self, category: str | None = None, topic: str | None = None) -> KnowledgeListResponse:
        docs = self._load()
        items: list[KnowledgeListItem] = []
        for d in docs:
            if category and d.category != category:
                continue
            if topic and (d.topic or d.category) != topic:
                continue
            items.append(
                KnowledgeListItem(
                    id=d.id, title=d.title, category=d.category,
                    topic=d.topic or d.category,
                    difficulty=d.difficulty, tags=d.tags,
                )
            )
        return KnowledgeListResponse(items=items, total=len(items))

    def get_knowledge(self, knowledge_id: str) -> KnowledgeDetail:
        for d in self._load():
            if d.id == knowledge_id:
                detail = self._to_detail(d)
                detail.learning_status = self._learning_status(knowledge_id)
                return detail
        raise RAGError(RAGErrorCode.knowledge_not_found, "知识点不存在")

    def _learning_status(self, knowledge_id: str) -> str:
        if self.db is None or not self.user_id:
            return "idle"
        try:
            row = self.db.execute(
                select(KnowledgeLearningRecord)
                .where(
                    KnowledgeLearningRecord.user_id == self.user_id,
                    KnowledgeLearningRecord.knowledge_point_id == knowledge_id,
                )
                .order_by(KnowledgeLearningRecord.id.desc())
            ).scalars().first()
        except SQLAlchemyError:
            return "idle"
        return row.status if row is not None else "idle"

    def _to_detail(self, doc: KnowledgeDocument) -> KnowledgeDetail:
        section_text: dict[str, str] = {}
        for title, text in _split_sections(doc.content):
            section_text[title] = text

        questions = _parse_questions(section_text.get(S_INTERVIEW_QUESTIONS, ""))
        answers = _parse_answers(section_text.get(S_REFERENCE_ANSWERS, ""))
        prerequisites = self._links(doc.dependencies)
        related = self._related(doc)

        return KnowledgeDetail(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            topic=doc.topic or doc.category,
            difficulty=doc.difficulty,
            tags=doc.tags,
            definition=(section_text.get(S_DEFINITION, "") or "").strip(),
            core_content=(section_text.get(S_CORE_CONTENT, "") or "").strip(),
            common_scenarios=_parse_bullets(section_text.get(S_COMMON_SCENARIOS, "")),
            pm_focus=_parse_bullets(section_text.get(S_PM_FOCUS, "")),
            interview_questions=_merge_qa(questions, answers),
            misconceptions=_parse_bullets(section_text.get(S_MISCONCEPTIONS, "")),
            prerequisites=prerequisites,
            related=related,
            cases=_parse_bullets(section_text.get(S_CASES, "")),
            related_questions=self._related_questions(doc, prerequisites, related),
        )

    # ================= P0-2：前置 / 相关 / 相关面试题 =================
    def _links(self, ids: list[str]) -> list[KnowledgeLink]:
        by_id = self._by_id()
        out: list[KnowledgeLink] = []
        for kid in ids:
            doc = by_id.get(kid)
            if doc is None:
                continue
            out.append(self._link(doc))
        return out

    @staticmethod
    def _link(doc: KnowledgeDocument) -> KnowledgeLink:
        return KnowledgeLink(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            topic=doc.topic or doc.category,
            difficulty=doc.difficulty,
        )

    def _related(self, doc: KnowledgeDocument, limit: int = MAX_RELATED_KNOWLEDGE) -> list[KnowledgeLink]:
        """从 Markdown 现有字段推导「相关知识点」，不新造数据。

        打分：共享 tag × 3 + 同 topic × 2 + 同 category × 1；排除自身与前置知识，
        按分数取前 5。这样即使知识库没有独立的 related 表，也能给出可解释的关联。
        """
        dep_ids = set(doc.dependencies)
        doc_tags = set(doc.tags)
        scored: list[tuple[int, int, int, int, KnowledgeDocument]] = []
        for idx, other in enumerate(self._load()):
            if other.id == doc.id or other.id in dep_ids:
                continue
            shared = len(doc_tags & set(other.tags))
            same_topic = 1 if doc.topic and other.topic == doc.topic else 0
            same_category = 1 if other.category == doc.category else 0
            score = shared * 3 + same_topic * 2 + same_category
            if score <= 0:
                continue
            scored.append((score, shared, same_topic, idx, other))
        scored.sort(key=lambda row: (-row[0], -row[1], -row[2], row[3]))
        return [self._link(row[4]) for row in scored[:limit]]

    def _related_questions(
        self,
        doc: KnowledgeDocument,
        prerequisites: list[KnowledgeLink],
        related: list[KnowledgeLink],
    ) -> list[KnowledgeRelatedQuestion]:
        """相关面试题：直接 core 优先，不足 5 条时用前置知识/相关知识关联题补齐。

        数据源优先 question_knowledge（DB），DB 不可用时回退 questions.json 的
        knowledge_ids；两种情况都只读，不写库。
        """
        questions = _question_map()
        if not questions:
            return []

        ordered: list[str] = []
        meta: dict[str, tuple[str, str]] = {}

        def add(question_id: str, relation: str, via_title: str = "") -> None:
            if question_id in meta or question_id not in questions:
                return
            meta[question_id] = (relation, via_title)
            ordered.append(question_id)

        rows = self._question_relations(doc.id)
        for row in rows:
            add(row.question_id, "core" if row.relation_type == "core" else row.relation_type)

        if len(ordered) < MAX_RELATED_QUESTIONS:
            for link in prerequisites:
                for row in self._question_relations(link.id):
                    add(row.question_id, "prerequisite", link.title)
                if len(ordered) >= MAX_RELATED_QUESTIONS:
                    break

        if len(ordered) < MAX_RELATED_QUESTIONS:
            for link in related:
                for row in self._question_relations(link.id):
                    add(row.question_id, "related", link.title)
                if len(ordered) >= MAX_RELATED_QUESTIONS:
                    break

        # DB 无关系（或测试环境未建表）时，用题库 knowledge_ids / knowledge_relations 兜底。
        if len(ordered) < MAX_RELATED_QUESTIONS:
            for question in questions.values():
                if _question_links(question, doc.id):
                    add(question["id"], "core")
            for link in prerequisites:
                for question in questions.values():
                    if _question_links(question, link.id):
                        add(question["id"], "prerequisite", link.title)
                if len(ordered) >= MAX_RELATED_QUESTIONS:
                    break

        out: list[KnowledgeRelatedQuestion] = []
        for question_id in ordered[:MAX_RELATED_QUESTIONS]:
            question = questions[question_id]
            relation, via_title = meta[question_id]
            out.append(
                KnowledgeRelatedQuestion(
                    id=question_id,
                    content=question.get("content", ""),
                    difficulty=question.get("difficulty", ""),
                    reference_answer=question.get("reference_answer", ""),
                    relation=relation,
                    via_title=via_title,
                )
            )
        return out

    def _question_relations(self, knowledge_id: str):
        """question_knowledge 中某知识点的题目关系；DB 不可用时返回空列表。"""
        if self.db is None or self._db_failed:
            return []
        try:
            rows = self.db.execute(
                select(QuestionKnowledge).where(QuestionKnowledge.knowledge_point_id == knowledge_id)
            ).scalars().all()
        except SQLAlchemyError:
            self._db_failed = True
            return []
        # core 优先；同关系类型按 id 稳定排序
        rows.sort(key=lambda row: (0 if row.relation_type == "core" else 1, row.id))
        return rows
