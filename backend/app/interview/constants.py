"""模拟面试模块常量（枚举值 + 轮次预算）。"""
from __future__ import annotations

# 面试配置枚举（值与前端 / API 使用的中文标签一致）
DIRECTIONS = ["C端产品经理", "B端产品经理", "AI产品经理", "数据产品经理"]
DIFFICULTIES = ["基础", "中等", "困难"]
INTERVIEW_TYPES = [
    "产品基础",
    "用户研究",
    "需求分析",
    "产品设计",
    "数据分析",
    "竞品分析",
    "商业化与增长",
    "AI产品",
    "项目复盘",
    "行为面试",
]

# 追问类型（受控枚举，LLM 只能从中选择）
FOLLOW_UP_TYPES = ["clarify", "deepen", "counter_example", "data", "scenario", "why"]

# Session 持久状态
STATUS_CREATED = "created"
STATUS_WAITING_ANSWER = "waiting_answer"
STATUS_COMPLETED = "completed"
STATUS_ABORTED = "aborted"
STATUS_FAILED = "failed"

# Turn 问题类型
QUESTION_TYPE_MAIN = "main"
QUESTION_TYPE_FOLLOW_UP = "follow_up"

# 结束原因
END_REASON_MAX_MAIN = "max_main_questions"
END_REASON_MANUAL = "manual"

# MVP 轮次预算（Step 8-1 §14）：5 个主问题，每题 0~2 个追问
DEFAULT_MAX_MAIN_QUESTIONS = 5
DEFAULT_MAX_FOLLOWUPS_PER_QUESTION = 2

# 回答长度上限（与 RAG query 上限一致）
MAX_ANSWER_LENGTH = 2000

# ---- 面试评价（Step 9-2）----

# 固定 5 个评价维度（顺序即报告展示顺序，与设计 §3 一致）
EVALUATION_DIMENSIONS = ["产品思维", "需求分析", "逻辑与表达", "AI知识", "业务意识"]

# 各维度权重（合计 1.0，与设计 §3 一致）
EVALUATION_WEIGHTS = {
    "产品思维": 0.30,
    "需求分析": 0.20,
    "逻辑与表达": 0.20,
    "AI知识": 0.15,
    "业务意识": 0.15,
}

# 弱项判定阈值：维度分数低于该值视为弱项（设计 §11）
WEAK_SCORE_THRESHOLD = 70

# 最多推荐知识点数（设计 §12）
MAX_RECOMMENDATIONS = 5

# 单条回答送入 LLM 评价前的截断长度（防超长输入，设计 §17）
MAX_EVAL_ANSWER_CHARS = 500

# 评价持久状态（design §7）：evaluating 为同步请求内瞬时态，不落库
EVAL_STATUS_PENDING = "pending"
EVAL_STATUS_COMPLETED = "completed"
EVAL_STATUS_FAILED = "failed"
