---
id: agent-human-confirmation
title: Agent关键动作确认机制
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 20
tags:
  - Agent
  - Human-in-the-loop
  - 用户确认
  - 高风险操作
dependencies:
  - agent-basics
  - tool-permission
  - ai-human-in-the-loop
---
# Agent关键动作确认机制

## 概述

对于具有明显副作用或较高风险的Agent动作，应该在执行前设置用户确认或人工审批节点。

## 定义

Agent关键动作确认是在人机协同流程中，对高风险Tool调用设置显式确认、审批或二次验证。

## 核心内容

可以按照风险划分：
确认界面应明确告诉用户：
Agent准备做什么
操作对象
影响范围
可能结果
是否可以撤销
避免：
“确认执行？”
却不告诉用户：
“到底执行什么”。

## 常见场景

- 企业Agent
- AI办公
- AI财务
- AI运营

## 产品经理关注点

- 用户确认不是形式按钮，而应该让用户真正理解即将发生的操作。

## 常见误区

- 所有Tool都需要确认
- 所有确认都能降低风险
- 确认弹窗越多越安全
- 用户确认后系统就不需要权限校验
