---
id: agent-observability
title: Agent可观测性
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 25
tags:
  - Agent
  - Observability
  - 日志
  - Tracing
  - 监控
dependencies:
  - agent-loop
  - agent-state-management
  - ai-cost
---
# Agent可观测性

## 概述

Agent行为具有多步骤和动态性，需要记录模型请求、工具调用、状态变化和错误，才能进行问题定位和效果分析。

## 定义

Agent可观测性是对Agent执行过程中的输入、输出、工具调用、状态、延迟、成本和错误进行记录和分析的能力。

## 核心内容

建议记录：
trace_id
task_id
step
model
prompt版本
tool
tool参数
tool结果
latency
token
cost
error
final_result
一个完整Trace可以帮助回答：
Agent为什么做了这个决定？
调用了哪个工具？
哪一步失败？
为什么成本突然增加？
哪个Prompt版本导致质量下降？
需要注意：
日志中可能包含敏感数据，因此可观测性也必须考虑数据脱敏和访问控制。

## 常见场景

- 企业Agent
- AI客服
- AI自动化

## 产品经理关注点

- 没有可观测性，Agent产品很难持续迭代。

## 常见误区

- 打印最终答案就是监控
- 日志越详细越好
- Trace不涉及隐私
- 监控只属于研发
