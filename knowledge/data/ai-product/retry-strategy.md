---
id: retry-strategy
title: AI请求重试策略
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 20
tags:
  - Retry
  - 重试
  - 容错
  - AI工程
dependencies:
  - ai-inference-basics
  - agent-idempotency
---
# AI请求重试策略

## 概述

AI系统中的重试应该针对可恢复错误设计，并控制次数、间隔和重复副作用。

## 定义

Retry是请求失败后按照预先定义的规则重新执行请求的机制。

## 核心内容

适合重试：
临时网络错误
Provider暂时不可用
Timeout
Rate Limit
不适合无限重试：
参数错误
权限错误
内容违规
明确业务错误
常见策略：
第一次失败
↓
等待
↓
Retry
↓
再次失败
↓
Fallback
可以使用：
Exponential Backoff
逐渐增加重试间隔。
对于Agent尤其需要考虑：
Tool是否已经成功执行？
否则可能出现：
Tool已经完成
↓
响应丢失
↓
Agent认为失败
↓
重复执行
因此Retry需要和Idempotency结合。

## 常见场景

- API调用
- Agent Tool
- RAG
- AI客服

## 产品经理关注点

- 重试解决的是暂时性失败，而不是所有失败。

## 常见误区

- 所有失败都应该重试
- 重试越多成功率越高
- Retry不会增加成本
- Retry不会产生副作用
