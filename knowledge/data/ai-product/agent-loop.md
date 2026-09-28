---
id: agent-loop
title: Agent执行循环
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 20
tags:
  - Agent Loop
  - 推理
  - Tool Calling
  - 状态
dependencies:
  - agent-basics
  - function-calling
  - state-design
---
# Agent执行循环

## 概述

Agent通常通过“思考/决策 → 工具调用 → 获取结果 → 再决策”的循环逐步完成复杂任务。

## 定义

Agent Loop是Agent根据当前状态不断选择下一步行动并执行，直到任务完成、失败或达到限制条件的过程。

## 核心内容

基本循环：
目标
↓
LLM
↓
Action
↓
Tool
↓
Observation
↓
LLM
↓
Action
↓
...
↓
Final Answer
系统必须设置终止条件：
任务完成
最大步骤数
最大Token
超时
工具连续失败
风险动作需要人工确认
用户主动终止
如果没有限制：
Agent可能进入循环，造成成本和延迟持续增加。

## 常见场景

- 研究Agent
- 数据分析Agent
- 企业自动化Agent

## 产品经理关注点

- Agent设计必须同时设计：
- 开始条件 + 执行过程 + 成功条件 + 失败条件 + 终止条件。

## 常见误区

- Agent应该一直执行直到完成
- Step越多能力越强
- 无限重试可以提高成功率
- Agent循环不需要状态管理
