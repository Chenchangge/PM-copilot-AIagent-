---
id: vector-database
title: 向量数据库
category: ai-product
topic: rag-retrieval
difficulty: 基础
estimated_minutes: 20
tags:
  - 向量数据库
  - Vector Database
  - Chroma
  - FAISS
  - RAG
dependencies:
  - embedding
  - rag-basics
---
# 向量数据库

## 概述

向量数据库用于存储向量及相关元数据，并支持相似性搜索，是RAG系统常见的基础设施组件。

## 定义

向量数据库是针对向量数据存储、索引和相似性搜索设计的数据系统。

## 核心内容

一个Chunk通常不仅存：
embedding
还应保存：
document_id
title
category
tags
source
chunk_id
content
version
permission
这样检索后才能知道：
“这个向量对应哪一份知识？”
常见能力：
向量检索
Metadata过滤
Top-K
删除/更新
Collection管理
常见技术：
Chroma
FAISS
Milvus
pgvector
Elasticsearch / OpenSearch相关向量能力

## 常见场景

- RAG
- 语义搜索
- 推荐
- 相似文档检索

## 产品经理关注点

- 向量数据库只是RAG基础设施的一部分，不等于RAG本身。

## 常见误区

- 使用Chroma就是实现RAG
- 向量数据库自动保证检索准确
- 向量数据库替代业务数据库
- 所有元数据都应该塞进Embedding
