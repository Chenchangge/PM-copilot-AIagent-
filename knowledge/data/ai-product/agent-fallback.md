---
id: agent-fallback
title: Agent回退与降级策略
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 20
tags:
  - Agent
  - Fallback
  - 降级
  - 容错
dependencies:
  - agent-error-handling
  - agent-human-confirmation
---
# Agent回退与降级策略

## 概述

Agent无法完成任务时应该有明确的降级路径，例如转人工、回到普通问答、提供部分结果或要求用户补充信息。

## 定义

Agent Fallback是Agent执行失败或无法确定下一步时，转向其他可控处理方式的机制。

## 核心内容

常见Fallback：
转人工
适用于高风险或复杂异常。
退回普通问答
适用于无法完成自动执行，但仍可提供信息。
提供部分结果
例如已经完成：
数据获取和分析，但报告生成失败。
请求用户补充
例如：
缺少订单号。
更换模型
在模型能力不足时切换其他模型。
结束任务
明确告诉用户当前无法完成。

## 常见场景

- 企业Agent
- AI客服
- AI办公

## 产品经理关注点

- 失败体验也属于产品设计的一部分。

## 常见误区

- Agent必须100%自动完成
- 失败后一直重试
- Fallback就是报错
- 转人工意味着Agent设计失败
