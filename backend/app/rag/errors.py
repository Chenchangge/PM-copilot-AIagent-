"""RAG 管线错误码。可读、可定位，且不泄露 Secret。"""
from enum import Enum


class RAGErrorCode(str, Enum):
    knowledge_load_error = "KNOWLEDGE_LOAD_ERROR"
    invalid_knowledge_metadata = "INVALID_KNOWLEDGE_METADATA"
    chunking_error = "CHUNKING_ERROR"
    embedding_model_not_found = "EMBEDDING_MODEL_NOT_FOUND"
    embedding_capability_unsupported = "EMBEDDING_CAPABILITY_UNSUPPORTED"
    embedding_api_key_missing = "EMBEDDING_API_KEY_MISSING"
    embedding_provider_error = "EMBEDDING_PROVIDER_ERROR"
    vector_db_error = "VECTOR_DB_ERROR"
    index_model_mismatch = "INDEX_MODEL_MISMATCH"
    # Step 7-2：Retriever
    retrieval_invalid_query = "RETRIEVAL_INVALID_QUERY"
    retrieval_invalid_top_k = "RETRIEVAL_INVALID_TOP_K"
    index_not_found = "INDEX_NOT_FOUND"
    retrieval_provider_error = "RETRIEVAL_PROVIDER_ERROR"
    retrieval_empty = "RETRIEVAL_EMPTY"
    # Step 7-3：Pipeline
    llm_model_not_found = "LLM_MODEL_NOT_FOUND"
    # Step 7-4：RAG API 请求校验
    retrieval_invalid_threshold = "RETRIEVAL_INVALID_THRESHOLD"
    retrieval_threshold_conflict = "RETRIEVAL_THRESHOLD_CONFLICT"
    # Step 10：Learning 知识详情不存在
    knowledge_not_found = "KNOWLEDGE_NOT_FOUND"


class RAGError(Exception):
    def __init__(self, code: RAGErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code.value}] {message}")
