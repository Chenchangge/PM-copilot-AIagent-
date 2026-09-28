---
id: retrieval
title: RAG检索
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 25
tags:
  - Retrieval
  - 检索
  - Top-K
  - RAG
dependencies:
  - embedding
  - vector-database
  - chunking-strategy
---
# RAG检索

## 概述

检索负责从知识库中找到与用户问题最相关的内容，是RAG系统最关键的中间环节之一。

## 定义

检索是根据用户Query，从知识库候选内容中选择可能支持回答的文档或Chunk的过程。

## 核心内容

基本流程：
Query
↓
Query处理
↓
候选召回
↓
相似度计算
↓
Top-K
↓
过滤/排序
↓
Context
常见检索方式：

## 常见场景

- 企业知识库
- 产品知识助手
- 技术文档搜索

## 产品经理关注点

- RAG问题应该区分：
- “没检索到”
“检索到了但没用好”
“知识本身错误”。

## 常见误区

- Top-K越大越好
- 相似度最高就是答案
- 检索到文档就代表回答正确
- LLM可以弥补所有检索错误
