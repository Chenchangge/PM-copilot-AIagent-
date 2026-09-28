---
id: guardrail-metrics
title: 护栏指标
category: strategy-product
topic: strategy-basics
difficulty: 进阶
estimated_minutes: 15
tags:
  - 护栏指标
  - Guardrail Metrics
  - 风险指标
  - 策略评估
dependencies:
  - strategy-objective-and-constraints
  - strategy-experiment
---
# 护栏指标

## 概述

护栏指标用于限制策略优化过程中不能接受的负面影响。

## 定义

护栏指标是实验或策略优化过程中，用于监控副作用和风险的辅助指标。

## 核心内容

例如：
目标：
提高内容点击率。
护栏：
举报率
不喜欢率
页面退出率
用户留存
内容质量
如果CTR上涨，但举报率明显上涨：
不能简单认为实验成功。
护栏指标可以帮助避免：
局部指标优化 → 整体产品受损。

## 常见场景

- 推荐
- 商业化
- 增长
- AI
- 风控

## 产品经理关注点

- 主指标回答“我们想获得什么”，护栏指标回答“为了这个目标什么不能牺牲”。

## 常见误区

- 护栏指标就是第二个主指标
- 护栏指标越多越好
- 护栏指标只用于安全问题
- 护栏指标不需要设阈值
