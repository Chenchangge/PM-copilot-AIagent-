---
id: agent-planning
title: Agent任务规划
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 25
tags:
  - Agent
  - Planning
  - 任务规划
  - LLM
dependencies:
  - agent-basics
  - workflow-vs-agent
  - agent-loop
---
# Agent任务规划

## 概述

任务规划是Agent将用户目标拆分成可执行步骤并确定执行顺序的过程。

## 定义

Agent Planning是模型或系统根据目标、约束和当前状态生成任务执行计划的机制。

## 核心内容

例如：
“帮我分析最近一个月销售数据，并找出下降原因。”
可能拆解为：
1. 获取销售数据
2. 清洗数据
3. 计算关键指标
4. 找出异常
5. 对异常进行分组
6. 生成分析结论
规划可以是：
预先规划
一次生成完整计划。
动态规划
执行一步后根据结果决定下一步。
动态规划更灵活，但不确定性也更高。

## 常见场景

- 数据分析Agent
- 研究Agent
- 企业自动化

## 产品经理关注点

- 产品经理需要判断任务是否适合让模型动态规划。

## 常见误区

- 所有任务都需要复杂Planning
- Planning越详细越好
- 模型生成的计划一定可执行
- Planning不需要约束
