---
id: rule-based-strategy
title: 规则策略
category: strategy-product
topic: strategy-basics
difficulty: 基础
estimated_minutes: 15
tags:
  - 规则
  - Rule
  - 策略引擎
  - 规则引擎
dependencies:
  - strategy-product-purpose
  - strategy-objective-and-constraints
---
# 规则策略

## 概述

规则策略通过明确的条件和动作实现可解释、可控制的业务决策。

## 定义

规则策略是按照预先定义的条件、优先级和动作执行决策的策略机制。

## 核心内容

基本结构：
IF 条件 → THEN 动作
例如：
如果用户连续7天未学习
→ 进入召回策略。
如果订单金额超过某阈值且风险等级较高
→ 进入人工审核。
规则通常包括：
条件
动作
优先级
生效范围
生效时间
版本
回滚
冲突处理

## 常见场景

- 风控
- 营销
- 用户运营
- 权限
- 推荐兜底

## 产品经理关注点

- 规则产品的重点是可配置性、可解释性和异常处理。

## 常见误区

- 规则越多越好
- 规则没有维护成本
- 规则一定比模型简单
- 只要条件正确就不会冲突
