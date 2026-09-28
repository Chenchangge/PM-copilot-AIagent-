---
id: task-success-rate
title: AI任务成功率
category: ai-product
topic: eval-reliability
difficulty: 基础
estimated_minutes: 15
tags:
  - AI评测
  - Task Success
  - 任务成功率
dependencies:
  - ai-evaluation-objective
---
# AI任务成功率

## 概述

任务成功率直接衡量AI是否完成了用户真正想完成的事情，比单纯评价语言质量更接近产品价值。

## 定义

任务成功率是满足预定义任务完成标准的任务数量占总测试任务数量的比例。

## 核心内容

基本计算：
任务成功率
=
成功完成任务数
÷
总任务数
例如：
100个真实任务
其中82个满足任务成功标准
Task Success Rate = 82%
任务成功标准必须提前定义。
例如AI学习助手：
用户是否获得正确答案并完成知识定位？
Agent：
是否完成指定任务且没有产生未授权副作用？
AI客服：
是否解决用户问题？

## 常见场景

- AI客服
- Agent
- AI学习助手
- AI办公

## 产品经理关注点

- 任务成功率应该和用户目标绑定。

## 常见误区

- 有答案就算任务成功
- 回答越长成功率越高
- 用户点赞率就是任务成功率
- Task Success可以完全脱离业务定义
