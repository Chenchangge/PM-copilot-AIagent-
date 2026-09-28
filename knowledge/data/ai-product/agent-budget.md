---
id: agent-budget
title: Agent成本与执行预算
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 20
tags:
  - Agent
  - 成本
  - Token
  - Step
  - Latency
dependencies:
  - agent-loop
  - ai-cost
  - ai-inference-basics
---
# Agent成本与执行预算

## 概述

Agent可能进行多轮模型调用和多次工具调用，因此需要对步骤、Token、时间和费用设置预算。

## 定义

Agent Budget是对Agent一次任务允许消耗的模型调用次数、执行步骤、Token、时间或费用进行限制的机制。

## 核心内容

Agent成本可能近似表现为：
单次任务成本
≈
模型调用次数 × 单次模型成本
+
工具调用成本
+
检索成本
+
基础设施成本
复杂Agent还可能出现：
失败
↓
重试
↓
再次调用
↓
继续执行
因此必须设置：
最大Step
最大Retry
最大Token
Timeout
单任务费用上限
Tool调用限制

## 常见场景

- 企业Agent
- AI研究
- AI数据分析

## 产品经理关注点

- 需要关注：
- “一次成功任务到底平均需要多少模型调用？”
- 而不是只看单次LLM API价格。

## 常见误区

- Agent成本就是一次模型调用
- 限制Step会严重降低所有Agent效果
- 无限Retry可以解决Agent失败
- Agent成本无法预测
