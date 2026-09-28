"""学习计划排课算法（确定性，§22）。LLM 不参与最终排课。

- 获取目标范围知识点 → 过滤 draft/deprecated → 依赖拓扑排序 → 按 difficulty/topic 排序
- 按 daily_minutes 贪心分配到 Day，不拆分单个知识点，尽量保持同 topic 相邻
- 生成 recommended_days = ceil(total_minutes / daily_minutes)
"""
from __future__ import annotations

import math

from app.learning.constants import RECOMMENDABLE_STATUSES
from app.learning.dependency import order_points
from app.learning.knowledge_index import KnowledgePointView


def filter_recommendable(points: list[KnowledgePointView]) -> list[KnowledgePointView]:
    """Learning Plan 默认只推荐 reviewed / verified（§13）。"""
    return [p for p in points if p.quality_status in RECOMMENDABLE_STATUSES]


def compute_total_minutes(points: list[KnowledgePointView]) -> int:
    return sum(p.estimated_minutes for p in points)


def compute_recommended_days(total_minutes: int, daily_minutes: int) -> int:
    if total_minutes <= 0:
        return 1
    return max(1, math.ceil(total_minutes / daily_minutes))


def schedule_points(points: list[KnowledgePointView]) -> list[KnowledgePointView]:
    """排序后的知识点（前置优先 + 难度 + topic）。"""
    return order_points(points)


def distribute(points: list[KnowledgePointView], daily_minutes: int, selected_days: int) -> list[list[KnowledgePointView]]:
    """把已排序知识点贪心分配到 selected_days 天（不拆分单个知识点）。

    前 selected_days-1 天尽量不超过 daily_minutes；最后一天吸收剩余（可超量）。
    返回恰好 selected_days 个 Day（尾部可能为空）。
    """
    n = max(1, selected_days)
    days: list[list[KnowledgePointView]] = [[] for _ in range(n)]
    day_i = 0
    day_used = 0
    for p in points:
        if day_i < n - 1 and day_used > 0 and day_used + p.estimated_minutes > daily_minutes:
            day_i += 1
            day_used = 0
        days[day_i].append(p)
        day_used += p.estimated_minutes
    return days
