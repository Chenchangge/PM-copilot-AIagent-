"""学习计划排课算法（确定性，§22）。LLM 不参与最终排课。

- 获取目标范围知识点 → 过滤 draft/deprecated → 按当前水平过滤难度 → 依赖拓扑排序
- 按「单日最大分钟数最小」做连续分段，不拆分单个知识点，保持同 topic 相邻
- 生成 recommended_days = ceil(total_minutes / effective_daily_minutes)
"""
from __future__ import annotations

import math

from app.learning.constants import (
    INTENSITY_FACTORS,
    LEVEL_DIFFICULTIES,
    MIN_DAILY_MINUTES,
    RECOMMENDABLE_STATUSES,
)
from app.learning.dependency import order_points
from app.learning.knowledge_index import KnowledgePointView


def filter_recommendable(points: list[KnowledgePointView]) -> list[KnowledgePointView]:
    """Learning Plan 默认只推荐 reviewed / verified（§13）。"""
    return [p for p in points if p.quality_status in RECOMMENDABLE_STATUSES]


def filter_by_level(points: list[KnowledgePointView], level: str) -> list[KnowledgePointView]:
    """按当前水平过滤知识点难度（P0-1：让「当前水平」真正生效）。

    难度是累积式：入门 = 入门/基础；基础 = 入门/基础/进阶；进阶 = 全部。
    """
    allowed = LEVEL_DIFFICULTIES.get(level)
    if allowed is None:
        return points
    return [p for p in points if p.difficulty in allowed]


def effective_daily_minutes(daily_minutes: int, intensity: str) -> int:
    """把「每日学习时间 × 学习强度」折算成真正的每日任务容量。

    轻量 0.7 / 标准 1.0 / 高强度 1.3，向上取整到 5 分钟，最低 5 分钟。
    """
    factor = INTENSITY_FACTORS.get(intensity, 1.0)
    raw = daily_minutes * factor
    return max(MIN_DAILY_MINUTES, int(math.ceil(raw / 5.0) * 5))


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
    """把已排序知识点按「单日分钟数尽量均衡」分配到 selected_days 天。

    旧实现用 daily_minutes 当硬上限，当用户选的天数小于自然所需天数时，最后一天会
    吸收全部剩余任务（实测 40 个知识点排 14 天时最后一天 260 分钟）。这里用动态规划
    做连续分段，最小化「单日最大分钟数」：
    - 保持知识点顺序与依赖顺序；
    - 不拆分单个知识点；
    - 天数多于知识点数时，前 m 天每天 1 个，其余为空（由调用方裁剪）。

    `daily_minutes` 保留在签名里用于调用方语义/兼容旧测试；实际分段由总时长和天数
    决定，结果会尽量贴近但不会机械地卡在 daily_minutes。
    """
    n = max(1, selected_days)
    m = len(points)
    days: list[list[KnowledgePointView]] = [[] for _ in range(n)]
    if m == 0:
        return days
    if n >= m:
        for i, point in enumerate(points):
            days[i] = [point]
        return days

    prefix = [0] * (m + 1)
    for i, p in enumerate(points, start=1):
        prefix[i] = prefix[i - 1] + p.estimated_minutes

    inf = float("inf")
    # dp_max[k][i]：前 i 个知识点分到 k 天时的最小「单日最大分钟数」；
    # dp_cost 用平方和做次级目标，避免出现「前几天 1 个任务、后几天 3 个任务」的
    # 锯齿分布（最大分钟数相同的前提下让每天尽量贴近平均值）。
    dp_max = [[inf] * (m + 1) for _ in range(n + 1)]
    dp_cost = [[inf] * (m + 1) for _ in range(n + 1)]
    cut = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, m + 1):
        dp_max[1][i] = prefix[i]
        dp_cost[1][i] = prefix[i] * prefix[i]
    for k in range(2, n + 1):
        for i in range(k, m + 1):
            best_max = inf
            best_cost = inf
            best_j = k - 1
            for j in range(k - 1, i):
                load = prefix[i] - prefix[j]
                value_max = max(dp_max[k - 1][j], load)
                value_cost = dp_cost[k - 1][j] + load * load
                if (value_max, value_cost) < (best_max, best_cost):
                    best_max = value_max
                    best_cost = value_cost
                    best_j = j
                elif (value_max, value_cost) == (best_max, best_cost):
                    # 多个分段的最优值相同时，取更接近「按比例分界」的切点，
                    # 避免高负载 Day 集中在前几天、后面全是很轻的 Day。
                    target_j = (i * (k - 1)) // k
                    if abs(j - target_j) < abs(best_j - target_j):
                        best_j = j
            dp_max[k][i] = best_max
            dp_cost[k][i] = best_cost
            cut[k][i] = best_j

    segments: list[tuple[int, int]] = []
    end = m
    for k in range(n, 0, -1):
        start = 0 if k == 1 else cut[k][end]
        segments.append((start, end))
        end = start
    segments.reverse()
    for day_index, (start, end) in enumerate(segments):
        days[day_index] = points[start:end]
    return days
