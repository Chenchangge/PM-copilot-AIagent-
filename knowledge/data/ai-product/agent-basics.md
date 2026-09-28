---
id: agent-basics
title: AI Agent基本概念
category: ai-product
topic: prompt-agent
difficulty: 基础
estimated_minutes: 20
tags:
  - Agent
  - AI Agent
  - 智能体
  - LLM
dependencies:
  - llm-basics
  - prompt-engineering
  - ai-product-value
---
# AI Agent基本概念

## 概述

AI Agent通常利用模型理解目标、制定步骤、调用工具并根据执行结果继续完成任务，是从“生成内容”向“完成任务”延伸的一类AI产品形态。

## 定义

AI Agent是能够基于目标进行一定程度的自主规划、决策，并调用工具或执行动作完成任务的AI系统。

## 核心内容

典型Agent链路：
用户目标
↓
任务理解
↓
规划
↓
选择工具
↓
执行
↓
观察结果
↓
判断是否完成
↓
继续执行 / 调整 / 结束
与普通Chatbot相比：
Chatbot：
问题 → 回答
Agent：
目标 → 规划 → 工具 → 观察 → 决策 → 行动
Agent通常包含：
LLM
Prompt
Tools
Memory / Context
Planner
Executor
State
Guardrails
Observability
但并不是所有复杂AI流程都需要Agent。

## 常见场景

- AI办公助手
- AI数据分析
- AI客服
- AI研究助手
- 企业自动化

## 产品经理关注点

- 产品经理首先需要判断：
- 用户到底需要“答案”，还是需要“完成任务”。

## 常见误区

- 使用Function Calling就是Agent
- Agent越自主越好
- 所有AI产品都应该Agent化
- Agent就是一个更大的Prompt
