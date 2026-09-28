---
id: agent-memory
title: Agent记忆机制
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 25
tags:
  - Agent Memory
  - Memory
  - 上下文
  - 个性化
dependencies:
  - agent-basics
  - token-and-context
---
# Agent记忆机制

## 概述

Agent记忆用于保存当前上下文之外、未来任务仍可能需要的信息，但不同类型的记忆需要明确生命周期和使用边界。

## 定义

Agent Memory是系统对过去交互、任务状态、用户偏好或长期知识进行保存，并在后续任务中按需调用的机制。

## 核心内容

可以区分：
短期记忆
当前任务和最近对话。
长期记忆
用户长期偏好、历史信息。
任务记忆
某个任务的中间状态。
外部知识
知识库中的稳定信息。
这些并不是同一种数据。
例如：
“用户喜欢简洁回答”
可能是长期偏好。
而：
“本次面试已经完成3道题”
属于任务状态。

## 常见场景

- AI助手
- AI学习助手
- AI办公
- 个性化Agent

## 产品经理关注点

- 记忆不是越多越好，需要考虑：
- 什么时候保存
- 保存什么
- 什么时候使用
- 用户是否知道
- 用户能否修改
- 数据生命周期

## 常见误区

- 保存全部聊天记录就是Memory
- Memory越多越好
- Memory和RAG完全相同
- 所有用户信息都应该永久保存
