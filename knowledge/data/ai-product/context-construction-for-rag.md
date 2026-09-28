---
id: context-construction-for-rag
title: RAG上下文构造
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 20
tags:
  - Context
  - Context Construction
  - RAG
  - Prompt
dependencies:
  - retrieval
  - token-and-context
  - ai-hallucination
---
# RAG上下文构造

## 概述

检索结果不能简单全部塞进Prompt，需要经过筛选、排序、去重和格式化后形成模型可利用的Context。

## 定义

RAG上下文构造是将检索得到的候选内容组织成最终提供给LLM的上下文信息的过程。

## 核心内容

可以包含：
System Instruction
+
User Query
+
Retrieved Evidence
+
Source Metadata
+
Conversation Context
需要考虑：
Top-K
排序
去重
来源
文档版本
内容长度
Chunk之间的关联
上下文优先级
例如Top-10检索结果中：
Chunk 1
Chunk 2
Chunk 3
Chunk 4
...
并不意味着全部都应该发送给模型。
过多无关内容可能：
增加Token成本
增加延迟
稀释关键证据
增加模型混淆

## 常见场景

- RAG
- 企业知识助手
- AI搜索

## 产品经理关注点

- RAG不是“检索越多越好”，而是“让模型看到最有用的信息”。

## 常见误区

- Top-K就是Context数量
- 检索结果可以原样拼接
- Context越多越准确
- 只需要关注Embedding
