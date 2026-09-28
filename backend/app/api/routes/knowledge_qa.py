"""知识库 AI 问答 API（Step 7-4）。

Route 保持薄层：HTTP → 校验 → build_rag_pipeline → run → 序列化。
不做 Retriever / Prompt / LLM / Context / Source Mapping（属于 RAG Layer）。

先校验请求、再解析模型：FastAPI 的 Depends 在函数体之前解析，若把 pipeline 建
成依赖，无效请求也会触发模型解析与索引连接；因此这里在函数体内、校验通过后再构建。
"""
import math

from fastapi import APIRouter, Depends

from app.api.routes.models import get_user_id
from app.rag.errors import RAGError, RAGErrorCode
from app.rag.pipeline import build_rag_pipeline
from app.rag.retriever import MAX_QUERY_LENGTH, MAX_TOP_K
from app.schemas.knowledge_qa import KnowledgeQARequest, KnowledgeQAResponse, to_qa_response

router = APIRouter()

# Chroma collection 使用 cosine 距离：similarity ∈ [0, 1]，distance ∈ [0, 2]（见 Step 7-2）。
SIMILARITY_RANGE = (0.0, 1.0)
DISTANCE_RANGE = (0.0, 2.0)


def _validate_request(request: KnowledgeQARequest) -> str:
    """API 层语义校验，返回 trim 后的 query。非法请求抛 RAGError → 统一错误映射。"""
    query = request.query.strip()
    if not query:
        raise RAGError(RAGErrorCode.retrieval_invalid_query, "query 不能为空")
    if len(query) > MAX_QUERY_LENGTH:
        raise RAGError(RAGErrorCode.retrieval_invalid_query, f"query 超过最大长度 {MAX_QUERY_LENGTH}")
    if request.top_k < 1 or request.top_k > MAX_TOP_K:
        raise RAGError(RAGErrorCode.retrieval_invalid_top_k, f"top_k 必须在 1～{MAX_TOP_K} 之间")
    if request.similarity_threshold is not None and request.max_distance is not None:
        raise RAGError(
            RAGErrorCode.retrieval_threshold_conflict,
            "similarity_threshold 与 max_distance 不能同时提供（两者表达同一过滤概念）。",
        )
    if request.similarity_threshold is not None:
        lo, hi = SIMILARITY_RANGE
        if not math.isfinite(request.similarity_threshold) or not (lo <= request.similarity_threshold <= hi):
            raise RAGError(
                RAGErrorCode.retrieval_invalid_threshold,
                f"similarity_threshold 必须是 {lo}～{hi} 之间的有限数字",
            )
    if request.max_distance is not None:
        lo, hi = DISTANCE_RANGE
        if not math.isfinite(request.max_distance) or not (lo <= request.max_distance <= hi):
            raise RAGError(
                RAGErrorCode.retrieval_invalid_threshold,
                f"max_distance 必须是 {lo}～{hi} 之间的有限数字",
            )
    return query


@router.post(
    "/qa",
    response_model=KnowledgeQAResponse,
    responses={
        400: {"description": "请求参数非法（query/top_k/threshold），或未配置 Embedding/文本生成模型"},
        404: {"description": "知识库索引不存在，需先构建索引"},
        409: {"description": "索引与当前 Embedding 模型不一致，需重建索引"},
        429: {"description": "上游模型服务限流"},
        502: {"description": "上游模型服务错误（API Key / 网络 / Provider 错误）"},
        504: {"description": "上游模型服务超时"},
        500: {"description": "服务端内部错误"},
    },
)
def knowledge_qa(
    request: KnowledgeQARequest,
    user_id: str = Depends(get_user_id),
) -> KnowledgeQAResponse:
    query = _validate_request(request)
    pipeline = build_rag_pipeline(user_id)
    result = pipeline.run(
        query=query,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        max_distance=request.max_distance,
    )
    return to_qa_response(result)
