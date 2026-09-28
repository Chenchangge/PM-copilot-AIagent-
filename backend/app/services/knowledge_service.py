"""知识库 Learning 服务：从 Markdown 加载并解析为结构化知识。

数据源原则（Step 10）：Markdown = Knowledge Source of Truth。本服务只读
`knowledge/data/*.md`，不新建 SQLite 表、不复制内容、不做 RAG。

复用 `MarkdownLoader`（front matter + H1 剥离），并在此做「## 章节 → 结构化字段」
的解析（章节标题来自审计结论，见 Step 10-1）。
"""
from __future__ import annotations

import re

from app.rag.document import KnowledgeDocument
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.loader import MarkdownLoader
from app.schemas.knowledge import (
    KnowledgeDetail,
    KnowledgeInterviewQuestion,
    KnowledgeListItem,
    KnowledgeListResponse,
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
    def __init__(self, loader: MarkdownLoader | None = None) -> None:
        self.loader = loader or MarkdownLoader()
        self._docs: list[KnowledgeDocument] | None = None

    def _load(self) -> list[KnowledgeDocument]:
        if self._docs is None:
            self._docs = self.loader.load()
        return self._docs

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
                return self._to_detail(d)
        raise RAGError(RAGErrorCode.knowledge_not_found, "知识点不存在")

    def _to_detail(self, doc: KnowledgeDocument) -> KnowledgeDetail:
        section_text: dict[str, str] = {}
        for title, text in _split_sections(doc.content):
            section_text[title] = text

        questions = _parse_questions(section_text.get(S_INTERVIEW_QUESTIONS, ""))
        answers = _parse_answers(section_text.get(S_REFERENCE_ANSWERS, ""))

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
        )
