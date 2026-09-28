---
id: prompt-injection
title: Prompt Injection与间接提示注入
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 25
tags:
  - Prompt Injection
  - Indirect Prompt Injection
  - AI安全
  - Agent
dependencies:
  - ai-security
  - function-calling
  - agent-product-boundary
---
# Prompt Injection与间接提示注入

## 概述

Prompt Injection是通过输入内容诱导模型改变原有任务、忽略规则或执行非预期行为的攻击方式。

## 定义

Prompt Injection是攻击者将恶意指令放入用户输入、网页、文档或其他模型可读取内容中，使模型产生非预期行为。

## 核心内容

分为：

## 常见场景

- AI搜索
- RAG
- Agent
- 企业AI

## 产品经理关注点

- 产品经理需要从：
- “模型听谁的？”
- 进一步思考：
- “系统真正允许模型做什么？”

## 常见误区

- 加一句System Prompt就能彻底解决
- 只有恶意用户输入才会导致Injection
- RAG不会发生Prompt Injection
- Injection只是模型问题
