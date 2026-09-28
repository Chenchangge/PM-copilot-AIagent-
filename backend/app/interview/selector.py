"""主问题选择器：按 direction / difficulty / interview_type 筛选，支持合理降级。"""
from __future__ import annotations

from app.interview.errors import InterviewError, InterviewErrorCode
from app.interview.question_bank import QuestionBank


class QuestionSelector:
    def __init__(self, bank: QuestionBank) -> None:
        self.bank = bank

    def select(
        self,
        direction: str,
        difficulty: str,
        interview_type: str,
        exclude_ids: set[str] | None = None,
    ) -> dict:
        """选择一个主问题。

        优先「方向 + 类型 + 难度」全匹配；无结果时逐级降级（方向 > 类型 > 难度），
        避免返回与面试方向完全无关的问题。已问过的题（exclude_ids）尽量避开。
        """
        exclude_ids = exclude_ids or set()

        # 逐级放宽过滤：优先保方向，其次类型，最后难度
        specs = [
            (direction, interview_type, difficulty),  # 全匹配
            (direction, interview_type, None),        # 去掉难度
            (direction, None, None),                  # 只保方向
            (None, interview_type, None),             # 只保类型
            (None, None, None),                       # 任意
        ]
        for d, t, diff in specs:
            pool = self._filter(d, t, diff)
            fresh = [q for q in pool if q["id"] not in exclude_ids]
            if fresh:
                return fresh[0]
            # 该过滤组合下候选都已使用：继续放宽过滤条件，绝不返回已使用过的题

        raise InterviewError(
            InterviewErrorCode.interview_question_bank_error,
            "题库中没有足够的未使用题目",
        )

    def _filter(self, direction: str | None, interview_type: str | None, difficulty: str | None) -> list[dict]:
        out: list[dict] = []
        for q in self.bank.all():
            if direction and direction not in q["directions"]:
                continue
            if interview_type and q["type"] != interview_type:
                continue
            if difficulty and q["difficulty"] != difficulty:
                continue
            out.append(q)
        return out
