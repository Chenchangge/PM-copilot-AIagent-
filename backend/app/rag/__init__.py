"""RAG 数据管线（Step 7-1：Indexing）。

Markdown → Loader → KnowledgeDocument → Chunker → Chunks → Embedding → Chroma。
本阶段只做索引构建，不实现 Retriever / Query / Chat（Step 7-2 / 7-3）。
"""
