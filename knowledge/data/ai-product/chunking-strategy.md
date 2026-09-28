---
id: chunking-strategy
title: RAG文本切分Chunking
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 25
tags:
  - Chunking
  - 文本切分
  - RAG
  - 上下文
dependencies:
  - rag-basics
  - document-cleaning-for-rag
  - token-and-context
---
# RAG文本切分Chunking

## 概述

Chunking将长文档拆成适合检索和上下文传递的内容片段，是RAG效果的重要影响因素。

## 定义

Chunking是将原始文档按照一定规则拆分成多个可检索文本块的过程。

## 核心内容

常见切分方法：
固定长度切分
按照字符或Token数量切分。
优点：
简单
可预测
缺点：
容易切断语义。
按标题切分
根据Markdown、HTML或文档标题层级切分。
优点：
保留结构。
语义切分
根据语义相似性决定边界。
优点：
更贴近语义。
缺点：
成本和实现复杂度更高。

## 常见场景

- 产品知识库
- 技术文档
- 企业知识库

## 产品经理关注点

- Chunking需要根据文档结构、查询类型和评测结果调整，而不是存在一个通用最佳值。

## 常见误区

- Chunk越小越好
- Chunk越大越好
- Overlap越大越准确
- 所有文档使用相同Chunk策略
