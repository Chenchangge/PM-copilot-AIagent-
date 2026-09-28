---
id: ai-cost
title: AI产品成本模型
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 25
tags:
  - AI成本
  - Token
  - 成本控制
  - LLM
dependencies:
  - ai-inference-basics
  - token-and-context
  - ai-evaluation-metrics
---
# AI产品成本模型

## 概述

AI产品成本不仅来自模型调用，还可能包括Embedding、向量数据库、搜索、Tool调用、GPU、网络、存储和人工审核等。

## 定义

AI产品成本模型是对完成一个用户任务所需的模型、基础设施和其他资源消耗进行拆解和计算的方法。

## 核心内容

一个AI产品的单次任务成本可能包括：
LLM Input Token
+
LLM Output Token
+
Embedding
+
Reranking
+
Search
+
Tool API
+
Infrastructure
+
Storage
+
Human Review
可以进一步计算：
单次任务成本
=
总成本
÷
有效完成任务数
例如：
1000次请求
→
1000次模型调用
→
其中300次还调用工具
→
其中100次触发额外搜索
不能简单使用：
模型单价 × 请求次数
作为完整成本。

## 常见场景

- AI客服
- AI Agent
- RAG
- AI搜索

## 产品经理关注点

- PM需要从“单次调用成本”进一步理解：
- 单个有效任务成本。

## 常见误区

- 模型API价格就是AI产品成本
- Token越少一定越好
- 便宜模型一定更适合
- 只看单次调用成本
