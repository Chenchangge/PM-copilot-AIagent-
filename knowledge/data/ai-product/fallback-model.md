---
id: fallback-model
title: AI模型降级与Fallback
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 20
tags:
  - Fallback
  - 降级
  - 容错
  - AI工程
dependencies:
  - ai-inference-basics
  - model-selection-for-pm
  - ai-evaluation
---
# AI模型降级与Fallback

## 概述

Fallback是在主模型或AI能力不可用、超时或质量不满足要求时，切换到备用方案的机制。

## 定义

AI Fallback是系统在主要AI路径失败时自动或半自动切换到其他模型、规则或产品流程的策略。

## 核心内容

可能的降级路径：
Model A
↓
失败
↓
Model B
↓
仍失败
↓
规则系统
↓
人工服务
Fallback触发条件可以包括：
Timeout
Rate Limit
Provider Error
Model unavailable
Invalid output
Safety failure
Tool failure
不同任务应该有不同Fallback。
例如：
AI客服无法回答
可能转：
人工客服。
而：
AI知识问答无法检索
可能返回：
“暂时无法找到可靠资料”。

## 常见场景

- AI客服
- AI Agent
- RAG
- AI面试

## 产品经理关注点

- Fallback不是简单“换一个模型”，而是设计用户在失败情况下仍然可以完成任务的路径。

## 常见误区

- Fallback一定是另一个模型
- 失败时重复调用同一个模型即可
- 所有错误都应该Fallback
- Fallback不需要监控
