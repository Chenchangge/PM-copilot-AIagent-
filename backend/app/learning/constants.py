"""学习计划与分类体系常量（Step 12-2-1 / 12-3 锁定的分类与枚举）。

注意：本模块定义「正式分类体系」（用于落库 / 未来外部知识库 ingestion）。
当前 45 个 MVP 知识点仍以 Markdown 的 legacy category（product/design/data/ai/
tools/interview）为准，Learning Plan 通过 legacy 兼容层读取，见 knowledge_index.py。
"""
from __future__ import annotations

# ---- 产品方向（一级方向，锁定 4 个，禁止新增）----
# 值即中文名，与 interview/questions.json 及前端保持一致
DIRECTIONS = ["C端产品经理", "B端产品经理", "AI产品经理", "数据产品经理"]

# ---- Specialization（不是一级方向，锁定 3 个）----
SPECIALIZATIONS = ["策略", "商业化", "行业/解决方案"]

# ---- 一级知识分类（锁定 11 个；工具不作为一级分类）----
# (slug, 中文名)
KNOWLEDGE_CATEGORIES = [
    ("product-foundation", "产品基础"),
    ("user-research", "用户研究"),
    ("product-design", "产品设计"),
    ("data-analysis", "数据分析"),
    ("user-growth", "用户增长"),
    ("commercialization", "商业化"),
    ("strategy-product", "策略产品"),
    ("b2b-enterprise", "B端/企业产品"),
    ("ai-product", "AI产品"),
    ("project-collaboration", "项目管理与协作"),
    ("interview-job", "面试与求职"),
]

# ---- 正式面试类型（锁定 10 个；「综合面试」是 InterviewMode，不是 InterviewType）----
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

# ---- 面试模式（综合面试属于模式，不是类型）----
INTERVIEW_MODES = ["专项面试", "综合面试"]

# ---- 二级主题（KnowledgeTopic seed；slug 稳定、幂等，三级结构 Category→Topic→Point）----
# (category_slug, topic_slug, topic_name)
KNOWLEDGE_TOPICS = [
    ("product-foundation", "pm-basics", "产品经理基础"),
    ("product-foundation", "requirements-value", "需求与价值"),
    ("user-research", "research-basics", "用户研究基础"),
    ("product-design", "requirements-doc", "需求文档"),
    ("product-design", "ia-flow", "信息架构与流程"),
    ("product-design", "interaction", "交互设计"),
    ("data-analysis", "core-metrics", "核心指标"),
    ("data-analysis", "analysis-methods", "分析方法"),
    ("data-analysis", "experimentation", "实验方法"),
    ("data-analysis", "data-tools", "数据工具"),
    ("user-growth", "growth-basics", "用户增长基础"),
    ("commercialization", "business-model", "商业模式"),
    ("ai-product", "llm-basics", "大模型基础"),
    ("ai-product", "rag-retrieval", "RAG与检索"),
    ("ai-product", "prompt-agent", "Prompt与Agent"),
    ("ai-product", "ai-engineering", "AI工程与成本性能"),
    ("ai-product", "eval-reliability", "评测与可靠性"),
    ("strategy-product", "strategy-basics", "策略产品基础"),
    ("b2b-enterprise", "b2b-basics", "B端产品基础"),
    ("project-collaboration", "project-tools", "项目管理工具"),
    ("interview-job", "self-introduction", "自我介绍"),
    ("interview-job", "interview-frameworks", "答题框架"),
]

# 分类/主题 slug → 中文名（供 Learning Plan 目标名解析）
CATEGORY_NAMES = dict(KNOWLEDGE_CATEGORIES)
TOPIC_NAMES = {slug: name for _, slug, name in KNOWLEDGE_TOPICS}
TOPIC_CATEGORY = {slug: cat for cat, slug, _ in KNOWLEDGE_TOPICS}

# 一级分类 → 建议的面试类型（阶段模拟面试预填，§31）
CATEGORY_INTERVIEW_TYPES = {
    "product-foundation": "产品基础",
    "user-research": "用户研究",
    "product-design": "产品设计",
    "data-analysis": "数据分析",
    "user-growth": "商业化与增长",
    "commercialization": "商业化与增长",
    "strategy-product": "产品设计",
    "b2b-enterprise": "需求分析",
    "ai-product": "AI产品",
    "project-collaboration": "项目复盘",
    "interview-job": "行为面试",
}

# ---- 知识点难度（KnowledgePoint.difficulty）----
DIFFICULTIES = ["入门", "基础", "进阶", "高级"]
DIFFICULTY_RANK = {"入门": 0, "基础": 1, "进阶": 2, "高级": 3}

# ---- 知识点质量状态（Learning Plan 默认只推荐 reviewed/verified）----
QUALITY_DRAFT = "draft"
QUALITY_REVIEWED = "reviewed"
QUALITY_VERIFIED = "verified"
QUALITY_DEPRECATED = "deprecated"
QUALITY_STATUSES = [QUALITY_DRAFT, QUALITY_REVIEWED, QUALITY_VERIFIED, QUALITY_DEPRECATED]
RECOMMENDABLE_STATUSES = {QUALITY_REVIEWED, QUALITY_VERIFIED}

# ---- estimated_minutes 允许值（与设计 §10 一致）----
ALLOWED_MINUTES = [5, 10, 15, 20, 30, 45, 60]
# 缺失 estimated_minutes 时按 difficulty 的保守回退值
DIFFICULTY_MINUTES = {"入门": 10, "基础": 15, "进阶": 20, "高级": 30}
# 较长正文（字符）在上表基础上追加的分钟数（保守、封顶）
LONG_CONTENT_CHARS = 4000
LONG_CONTENT_BONUS_MINUTES = 10

# ---- estimated_minutes_source ----
MINUTES_SOURCE_MANUAL = "manual"
MINUTES_SOURCE_AI = "ai_estimated"
MINUTES_SOURCE_FALLBACK = "fallback"

# ---- QuestionKnowledge relation_type ----
RELATION_CORE = "core"
RELATION_RELATED = "related"
RELATION_PREREQUISITE = "prerequisite"

# ---- 学习目标类型（target_type）----
TARGET_TYPE_CATEGORY = "category"
TARGET_TYPE_TOPIC = "topic"
TARGET_TYPE_TAG = "tag"
TARGET_TYPE_DIRECTION = "direction"
# 路径（LEARNING_PATHS）作为整体目标落库时使用；仅由 path_id 入口产生，不对外暴露为普通目标类型。
TARGET_TYPE_PATH = "path"
TARGET_TYPES = [
    TARGET_TYPE_CATEGORY,
    TARGET_TYPE_TOPIC,
    TARGET_TYPE_TAG,
    TARGET_TYPE_DIRECTION,
    TARGET_TYPE_PATH,
]

# ---- 方向 → 相关一级分类（Direction 作为方向型学习目标时解析范围）----
# 列表顺序即优先级：首项为该方向的「标志性」分类（用于阶段模拟面试类型推荐）。
DIRECTION_CATEGORIES = {
    "C端产品经理": ["product-foundation", "user-research", "product-design", "user-growth", "data-analysis"],
    "B端产品经理": ["b2b-enterprise", "product-foundation", "product-design", "project-collaboration", "user-research"],
    "AI产品经理": ["ai-product", "product-foundation", "data-analysis", "user-research"],
    "数据产品经理": ["data-analysis", "product-foundation", "user-growth", "commercialization"],
}

# ---- 学习计划配置枚举 ----
CURRENT_LEVELS = ["入门", "基础", "进阶"]
DAILY_MINUTES_OPTIONS = [15, 30, 45, 60]
INTENSITIES = ["轻量", "标准", "高强度"]
# 手动可选学习周期（天）
DAY_CHOICES = [5, 7, 10, 14]

# ---- 当前水平 → 允许的知识点难度（累积式：越高阶覆盖越多）----
# 入门用户先从「入门 + 基础」开始；「基础」再放开进阶；「进阶」放开全部。
# 这样既满足「当前水平真实影响知识点数量」，也不会让入门用户直接看到高级内容。
LEVEL_DIFFICULTIES = {
    "入门": {"入门", "基础"},
    "基础": {"入门", "基础", "进阶"},
    "进阶": set(DIFFICULTIES),
}

# ---- 学习强度 → 有效每日学习量系数（真正参与排课）----
# 轻量 = 每日时长 × 0.7；标准 = × 1.0；高强度 = × 1.3。
# 折算后向上取整到 5 分钟粒度，避免出现 21/39 分钟这类不可执行的日任务量。
INTENSITY_FACTORS = {"轻量": 0.7, "标准": 1.0, "高强度": 1.3}
MIN_DAILY_MINUTES = 5

# ---- 计划 / Day / Task / Record 状态 ----
PLAN_DRAFT = "draft"
PLAN_ACTIVE = "active"
PLAN_PAUSED = "paused"
PLAN_COMPLETED = "completed"
PLAN_ABANDONED = "abandoned"

DAY_LOCKED = "locked"
DAY_AVAILABLE = "available"
DAY_IN_PROGRESS = "in_progress"
DAY_COMPLETED = "completed"
DAY_SKIPPED = "skipped"

TASK_PENDING = "pending"
TASK_IN_PROGRESS = "in_progress"
TASK_COMPLETED = "completed"
TASK_SKIPPED = "skipped"

RECORD_STARTED = "started"
RECORD_COMPLETED = "completed"

# ---- 面试推荐门槛：目标范围内完成比例 >= 该阈值时提示「阶段模拟面试」----
INTERVIEW_RECOMMEND_RATIO = 0.70

# ---- 依赖关系相关 ----
RELATED_RELATION_TYPES = ["related", "similar", "supersedes", "deprecated_by"]

# ---- 当前 legacy Markdown 分类（Learning Plan MVP 直接使用的目标分类）----
# slug -> 中文标签（与 frontend/src/utils/knowledge.js 保持一致）
LEGACY_CATEGORY_LABELS = {
    "product": "产品基础",
    "design": "产品设计",
    "data": "数据分析",
    "ai": "AI产品",
    "tools": "工具",
    "interview": "面试与求职",
}

# 旧计划任务里残留的历史知识点 ID（内容迁移后已不在 Markdown 索引）→ 展示标题。
# 仅作为接口 title 的最后回退，不改变计划/任务数据。
LEGACY_KNOWLEDGE_TITLES = {
    "user-persona": "用户画像",
    "user-requirements": "用户需求",
    "user-value": "用户价值",
    "product-goals": "产品目标",
    "pm-responsibilities": "产品经理职责",
}

# ---- 学习路径（P0-1：把「内容分类」入口改成「学习目标」入口）----
# 只做目标聚合，不新造知识点：target_type + target_ids 用现有 resolve_target 解析。
# days_hint 是产品定义的建议冲刺周期；实际天数仍由后端按当前水平/每日时长/强度计算。
LEARNING_PATHS = [
    {
        "id": "ai-pm-sprint",
        "name": "AI 产品经理 · 面试速成",
        "subtitle": "大模型 · RAG · AI 工程核心知识",
        "target_type": TARGET_TYPE_TOPIC,
        "target_ids": ["llm-basics", "rag-retrieval", "ai-engineering"],
        "days_hint": 14,
        "direction": "AI产品经理",
        "interview_types": ["AI产品"],
    },
    {
        "id": "product-foundation-track",
        "name": "产品基础 · 系统打底",
        "subtitle": "产品基础 + 需求 + 设计",
        "target_type": TARGET_TYPE_CATEGORY,
        "target_ids": ["product-foundation", "product-design", "user-research"],
        "days_hint": 21,
        "direction": "C端产品经理",
        "interview_types": ["产品基础", "需求分析", "产品设计", "用户研究"],
    },
    {
        "id": "interview-sprint",
        "name": "面试冲刺",
        "subtitle": "面试与求职 + 答题框架",
        "target_type": TARGET_TYPE_CATEGORY,
        "target_ids": ["interview-job"],
        "days_hint": 7,
        "direction": None,
        "interview_types": ["行为面试"],
    },
]
LEARNING_PATHS_BY_ID = {p["id"]: p for p in LEARNING_PATHS}

# 学习计划首屏只露 5 个分类；其余折叠到「更多分类」。
# 顺序按产品相关性固定，不按知识点数量排序（AI产品数量最多但不该排第一）。
PLAN_FEATURED_CATEGORIES = [
    "product-foundation",
    "data-analysis",
    "ai-product",
    "user-research",
    "interview-job",
]
