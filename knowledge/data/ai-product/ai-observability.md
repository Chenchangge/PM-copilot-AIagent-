---
id: ai-observability
title: AI系统可观测性
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 25
tags:
  - Observability
  - Trace
  - 日志
  - AI工程
dependencies:
  - ai-inference-basics
  - ai-evaluation
  - agent-observability
---
# AI系统可观测性

## 概述

AI系统可观测性需要让团队能够知道一次AI任务经历了什么、为什么失败以及成本和性能消耗在哪里。

## 定义

AI Observability是对AI系统请求、模型、Prompt、检索、Tool、输出和错误进行记录、追踪和分析的能力。

## 核心内容

一个RAG请求可能记录：
Request ID
↓
User Query
↓
Retriever
↓
Top-K
↓
Reranker
↓
Prompt Version
↓
Model
↓
Input Tokens
↓
Output Tokens
↓
Latency
↓
Answer
↓
Citation
Agent还应该记录：
Agent Step 1
↓
Tool A
↓
Agent Step 2
↓
Tool B
↓
Final Answer
需要注意隐私：
日志本身可能包含敏感数据。
因此不能简单地“全部记录”。

## 常见场景

- RAG
- Agent
- AI客服
- AI搜索

## 产品经理关注点

- 没有可观测性，就很难回答：
- “用户为什么得到这个答案？”

## 常见误区

- 日志越多越好
- 只记录最终答案就够
- Trace只属于研发
- 监控只看接口是否200
