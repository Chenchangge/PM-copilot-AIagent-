---
id: reranking
title: RAG重排序Rerank
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 20
tags:
  - Rerank
  - 重排序
  - Retrieval
  - RAG
dependencies:
  - retrieval
---
# RAG重排序Rerank

## 概述

Rerank在初步召回候选内容后进一步判断Query与候选文档之间的相关性，从而提高进入最终Context的内容质量。

## 定义

Rerank是对初始检索结果再次排序的过程。

## 核心内容

典型流程：
Query
↓
初步召回
↓
Top 20 / Top 50
↓
Rerank
↓
Top 3 / Top 5
↓
LLM
为什么需要Rerank？
向量检索通常适合：
快速召回候选。
但“语义相似”不完全等于：
“能够回答当前问题”。
Rerank可以从更精细的Query-Document相关性角度重新判断。
代价：
增加计算
增加延迟
增加系统复杂度
因此是否加入Rerank需要实际评测。

## 常见场景

- 企业搜索
- 专业知识库
- RAG
- 长文档问答

## 产品经理关注点

- Rerank是典型的“质量—成本—延迟”权衡点。

## 常见误区

- Rerank一定需要
- Rerank一定提高最终答案
- Rerank可以修复错误Chunk
- Rerank越强越好
