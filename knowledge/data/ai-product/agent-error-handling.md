---
id: agent-error-handling
title: Agent错误处理与重试
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 25
tags:
  - Agent
  - Error Handling
  - Retry
  - Fault Tolerance
dependencies:
  - agent-loop
  - function-calling
  - ai-human-in-the-loop
---
# Agent错误处理与重试

## 概述

Agent执行链路中任何一步都可能失败，因此需要区分可重试错误、不可重试错误和需要人工介入的错误。

## 定义

Agent错误处理是对模型、工具、网络、权限、数据等异常进行分类，并采取重试、回退、暂停或终止策略。

## 核心内容

错误可以分为：

## 常见场景

- Agent工具调用
- 企业自动化
- AI客服

## 产品经理关注点

- 错误处理的核心不是“让Agent一直重试”，而是：
- 让系统知道什么时候应该继续、回退、等待人类或停止。

## 常见误区

- 所有错误都应该Retry
- Retry越多成功率越高
- Tool失败等于模型失败
- Agent应该自动解决所有错误
