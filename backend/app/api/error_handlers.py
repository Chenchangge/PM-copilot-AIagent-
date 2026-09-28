"""RAG / 面试错误 → HTTP 状态码的统一映射 + 异常处理器。

统一错误响应格式：{"error": {"code": "...", "message": "..."}}。
绝不泄漏 API Key / traceback / 服务器内部路径。
"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import AIErrorCode
from app.interview.errors import InterviewError, InterviewErrorCode
from app.learning.errors import LearningError, LearningErrorCode
from app.rag.errors import RAGError, RAGErrorCode

# 400 —— 客户端请求 / 配置问题（可自行修复）
# 404 / 409 —— 索引资源缺失 / 状态冲突（需先构建或重建索引）
# 429 / 502 / 504 —— 上游模型服务（BYOK）：限流 / 网关错误 / 网关超时
# 500 —— 服务端内部错误
_STATUS_BY_CODE: dict[str, int] = {
    RAGErrorCode.retrieval_invalid_query.value: 400,
    RAGErrorCode.retrieval_invalid_top_k.value: 400,
    RAGErrorCode.retrieval_invalid_threshold.value: 400,
    RAGErrorCode.retrieval_threshold_conflict.value: 400,
    RAGErrorCode.knowledge_not_found.value: 404,
    RAGErrorCode.embedding_capability_unsupported.value: 400,
    RAGErrorCode.embedding_model_not_found.value: 400,
    RAGErrorCode.llm_model_not_found.value: 400,
    RAGErrorCode.index_not_found.value: 404,
    RAGErrorCode.index_model_mismatch.value: 409,
    RAGErrorCode.retrieval_provider_error.value: 502,
    RAGErrorCode.embedding_provider_error.value: 502,
    RAGErrorCode.vector_db_error.value: 500,
    AIErrorCode.invalid_api_key.value: 502,
    AIErrorCode.model_not_found.value: 502,
    AIErrorCode.invalid_base_url.value: 502,
    AIErrorCode.network_error.value: 502,
    AIErrorCode.provider_error.value: 502,
    AIErrorCode.rate_limited.value: 429,
    AIErrorCode.timeout.value: 504,
    AIErrorCode.unknown.value: 500,
    # 面试业务错误（Step 8-2）
    InterviewErrorCode.interview_model_not_found.value: 400,
    InterviewErrorCode.interview_invalid_answer.value: 400,
    InterviewErrorCode.interview_session_not_found.value: 404,
    InterviewErrorCode.interview_session_completed.value: 409,
    InterviewErrorCode.interview_invalid_state.value: 409,
    InterviewErrorCode.interview_structured_output_error.value: 502,
    InterviewErrorCode.interview_question_bank_error.value: 500,
    # 面试评价（Step 9-2）
    InterviewErrorCode.evaluation_not_found.value: 404,
    InterviewErrorCode.evaluation_failed.value: 502,
    # 学习计划（Step 12-3）
    LearningErrorCode.learning_invalid_target_type.value: 400,
    LearningErrorCode.learning_invalid_level.value: 400,
    LearningErrorCode.learning_invalid_minutes.value: 400,
    LearningErrorCode.learning_invalid_intensity.value: 400,
    LearningErrorCode.learning_invalid_days.value: 400,
    LearningErrorCode.learning_invalid_direction.value: 400,
    LearningErrorCode.learning_target_not_found.value: 404,
    LearningErrorCode.learning_target_empty.value: 404,
    LearningErrorCode.learning_knowledge_not_found.value: 404,
    LearningErrorCode.learning_dependency_cycle.value: 409,
    LearningErrorCode.learning_plan_not_found.value: 404,
    LearningErrorCode.learning_plan_state.value: 409,
    LearningErrorCode.learning_task_not_found.value: 404,
    LearningErrorCode.learning_task_state.value: 409,
}


def _code_str(code) -> str:
    return code.value if hasattr(code, "value") else str(code)


def rag_error_handler(_: Request, exc: RAGError) -> JSONResponse:
    code = _code_str(exc.code)
    status = _STATUS_BY_CODE.get(code, 500)
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": exc.message}})


def interview_error_handler(_: Request, exc: InterviewError) -> JSONResponse:
    code = _code_str(exc.code)
    status = _STATUS_BY_CODE.get(code, 500)
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": exc.message}})


def learning_error_handler(_: Request, exc: LearningError) -> JSONResponse:
    code = _code_str(exc.code)
    status = _STATUS_BY_CODE.get(code, 500)
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": exc.message}})
