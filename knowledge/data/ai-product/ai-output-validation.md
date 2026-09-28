---
id: ai-output-validation
title: AI输出校验
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 20
tags:
  - Structured Output
  - Output Validation
  - AI工程
  - 数据校验
dependencies:
  - structured-output
  - ai-evaluation
---
# AI输出校验

## 概述

AI输出不能天然视为可靠数据，需要通过Schema、规则和业务逻辑进行校验。

## 定义

AI输出校验是对模型生成结果进行结构、格式、类型、内容和业务规则检查的过程。

## 核心内容

可以分层：

## 常见场景

- AI评分
- Agent
- RAG
- AI表单

## 产品经理关注点

- 结构化输出的价值不仅是“方便前端解析”，更重要的是把AI输出纳入系统控制。

## 常见误区

- Structured Output天然保证内容正确
- JSON合法就代表业务正确
- Prompt要求格式就不需要后端校验
- 校验失败可以无限Retry
