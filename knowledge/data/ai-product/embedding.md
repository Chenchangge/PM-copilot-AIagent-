---
id: embedding
title: Embedding向量表示
category: ai-product
topic: rag-retrieval
difficulty: 基础
estimated_minutes: 20
tags:
  - Embedding
  - 向量
  - 语义搜索
  - RAG
dependencies:
  - rag-basics
  - llm-basics
---
# Embedding向量表示

## 概述

Embedding将文本转换成向量，使系统能够通过向量空间中的相似性进行语义检索。

## 定义

Embedding是将文本、图片或其他数据转换成数值向量表示的过程。

## 核心内容

例如：
“如何计算用户留存率？”
↓
Embedding模型
↓
[0.12, -0.31, 0.77, ...]
知识文档也会转换成向量。
用户查询和知识Chunk经过Embedding后，可以计算相似程度。
常见相似度：
Cosine Similarity
Dot Product
Euclidean Distance
产品经理需要理解：
Embedding不是“理解答案”，而是提供语义表示，用于检索或其他下游任务。

## 常见场景

- 语义搜索
- RAG
- 推荐
- 相似内容查找
- 文档聚类

## 产品经理关注点

- Embedding模型选择也应该通过实际检索任务评测，而不是只看模型名称或维度。

## 常见误区

- 向量就是知识
- 向量数据库能理解问题
- 向量维度越大一定越准确
- Embedding可以替代LLM
