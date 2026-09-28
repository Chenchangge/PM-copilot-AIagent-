"""知识库 Learning API 的响应 Schema。

命名遵循项目现有 API 风格（snake_case），与 Evaluation 推荐的 knowledge_id
（slug）保持一致；前后端统一使用 slug 作为真实知识 ID。
"""
from pydantic import BaseModel, Field


class KnowledgeListItem(BaseModel):
    id: str
    title: str
    category: str = ""
    topic: str = ""
    difficulty: str = ""
    tags: list[str] = Field(default_factory=list)


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeListItem] = Field(default_factory=list)
    total: int = 0


class KnowledgeInterviewQuestion(BaseModel):
    """面试问题 + 对应参考答案（按顺序合并，见 Step 10-2 §7.6）。"""

    question: str
    reference_answer: str = ""


class KnowledgeDetail(BaseModel):
    id: str
    title: str
    category: str = ""
    topic: str = ""
    difficulty: str = ""
    tags: list[str] = Field(default_factory=list)
    definition: str = ""
    core_content: str = ""  # 保留为 Markdown 字符串，前端渲染
    common_scenarios: list[str] = Field(default_factory=list)
    pm_focus: list[str] = Field(default_factory=list)
    interview_questions: list[KnowledgeInterviewQuestion] = Field(default_factory=list)
