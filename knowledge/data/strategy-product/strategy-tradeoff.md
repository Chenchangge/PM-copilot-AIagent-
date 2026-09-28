---
id: strategy-tradeoff
title: 策略中的多目标取舍
category: strategy-product
topic: strategy-basics
difficulty: 高级
estimated_minutes: 20
tags:
  - 多目标
  - Trade-off
  - 策略取舍
  - 业务目标
dependencies:
  - strategy-objective-and-constraints
  - guardrail-metrics
  - strategy-experiment
---
# 策略中的多目标取舍

## 概述

策略产品通常同时面对多个目标，不同目标之间可能发生冲突，因此需要明确优先级和约束。

## 定义

策略中的多目标取舍，是在用户价值、业务收益、效率、风险等多个目标之间建立优先级和约束的过程。

## 核心内容

例如电商推荐：
提高GMV可能意味着：
更多高价商品曝光
但可能影响：
用户满意度
商品多样性
长期留存
因此不能只问：
哪个指标最高？
而应该问：
当前业务阶段的主要目标是什么？哪些指标属于硬约束？哪些指标可以接受短期波动？
可以建立：
主目标 → 次目标 → 护栏 → 风险阈值

## 常见场景

- 推荐
- 搜索
- 商业化
- 广告
- AI产品

## 产品经理关注点

- 产品经理的核心工作之一是把“模糊的业务目标冲突”转化成可执行的策略优先级。

## 常见误区

- 所有指标都应该同时最大化
- 可以完全依靠算法解决价值冲突
- 主指标最高就是最优策略
- 业务目标不会变化
