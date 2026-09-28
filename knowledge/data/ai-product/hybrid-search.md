---
id: hybrid-search
title: RAG混合检索
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 20
tags:
  - Hybrid Search
  - 混合检索
  - BM25
  - 向量检索
dependencies:
  - retrieval
  - embedding
---
# RAG混合检索

## 概述

混合检索结合关键词匹配和向量语义检索，可以同时利用精确词项匹配和语义相关性。

## 定义

混合检索是将多种检索方法组合使用的检索策略。

## 核心内容

例如用户查询：
“text-embedding-v4 的1024维Embedding配置”
纯语义检索可能理解整体语义。
关键词检索则可能更容易命中：
text-embedding-v4
1024
Embedding
混合检索能够兼顾：
关键词精确匹配
和
语义相似匹配。
常见组合：
BM25
+
Vector Search
+
Rerank

## 常见场景

- 技术文档
- 产品文档
- 企业知识库
- 专业搜索

## 产品经理关注点

- 专业知识库中，专有名词、编号、产品名称、错误代码等往往需要精确匹配。

## 常见误区

- 向量搜索一定比关键词搜索好
- 混合检索一定提升效果
- 关键词检索已经过时
- 混合检索不增加复杂度
