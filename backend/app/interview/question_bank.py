"""面试题库加载与结构校验。

题库是静态 JSON（interview/data/questions.json），独立于知识库 knowledge/data/。
本模块只负责「读 + 校验」，不涉及 LLM / 检索。
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import PROJECT_ROOT
from app.interview.constants import DIFFICULTIES, DIRECTIONS, INTERVIEW_TYPES
from app.interview.errors import InterviewError, InterviewErrorCode

INTERVIEW_DATA_DIR = PROJECT_ROOT / "interview" / "data"
QUESTIONS_FILE = INTERVIEW_DATA_DIR / "questions.json"

REQUIRED_FIELDS = [
    "id",
    "content",
    "type",
    "difficulty",
    "directions",
    "knowledge_ids",
    "evaluation_points",
    "reference_answer",
]


class QuestionBank:
    """面试题库。load() 后可通过 all() / get() / count() 访问。"""

    def __init__(self, path: Path | str = QUESTIONS_FILE) -> None:
        self.path = Path(path)
        self._questions: list[dict] = []
        self._by_id: dict[str, dict] = {}

    def load(self) -> list[dict]:
        if not self.path.exists():
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                f"面试题库不存在：{self.path}",
            )
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                "面试题库 JSON 解析失败",
            ) from exc
        if not isinstance(data, list) or not data:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                "面试题库为空或格式错误",
            )

        self._questions = data
        self._by_id = {}
        for q in data:
            self._validate(q)
            if q["id"] in self._by_id:
                raise InterviewError(
                    InterviewErrorCode.interview_question_bank_error,
                    f"题目 ID 重复：{q['id']}",
                )
            self._by_id[q["id"]] = q
        return self._questions

    def _validate(self, q: dict) -> None:
        if not isinstance(q, dict):
            raise InterviewError(InterviewErrorCode.interview_question_bank_error, "题目条目必须是对象")
        for field in REQUIRED_FIELDS:
            if field not in q:
                raise InterviewError(
                    InterviewErrorCode.interview_question_bank_error,
                    f"题目缺少字段：{field}（id={q.get('id', '?')}）",
                )
        if q["type"] not in INTERVIEW_TYPES:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                f"非法 type：{q['type']}（id={q['id']}）",
            )
        if q["difficulty"] not in DIFFICULTIES:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                f"非法 difficulty：{q['difficulty']}（id={q['id']}）",
            )
        if not isinstance(q["directions"], list) or not q["directions"]:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                f"directions 必须为非空数组（id={q['id']}）",
            )
        for d in q["directions"]:
            if d not in DIRECTIONS:
                raise InterviewError(
                    InterviewErrorCode.interview_question_bank_error,
                    f"非法 direction：{d}（id={q['id']}）",
                )
        if not isinstance(q["knowledge_ids"], list) or not q["knowledge_ids"]:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                f"knowledge_ids 必须为非空数组（id={q['id']}）",
            )
        if not isinstance(q["evaluation_points"], list) or not q["evaluation_points"]:
            raise InterviewError(
                InterviewErrorCode.interview_question_bank_error,
                f"evaluation_points 必须为非空数组（id={q['id']}）",
            )

    def all(self) -> list[dict]:
        return list(self._questions)

    def get(self, question_id: str) -> dict | None:
        return self._by_id.get(question_id)

    def count(self) -> int:
        return len(self._questions)
