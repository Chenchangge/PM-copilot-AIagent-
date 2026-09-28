---
id: metric-decomposition
title: 指标拆解
category: data-analysis
topic: core-metrics
difficulty: 进阶
estimated_minutes: 15
tags:
  - 指标拆解
  - Metric Tree
  - 指标树
  - 业务分析
dependencies:
  - metric-definition-and-dimension
  - product-metrics-basics
---
# 指标拆解

## 概述

指标拆解是把一个结果指标逐层拆成能够解释和影响它的组成因素。

## 定义

通过数学关系、业务流程或用户行为，将宏观指标拆解成更具体的子指标。

## 核心内容

例如：
收入 = 付费用户数 × ARPPU
继续拆：
付费用户数 = 活跃用户数 × 付费转化率
于是：
收入 = 活跃用户数 × 付费转化率 × ARPPU
如果收入下降，就可以进一步检查：
活跃用户下降？
付费转化率下降？
客单价下降？
指标拆解的前提是：
变量之间存在合理关系
口径一致
数据可获得

## 常见场景

- 收入下降
- GMV下降
- DAU变化
- 转化率异常
- 经营分析

## 产品经理关注点

- 指标拆解可以帮助产品经理把“结果问题”转化成可行动的问题。

## 常见误区

- 指标树越复杂越好
- 所有指标都能数学拆解
- 找到下降指标就等于找到原因
- 指标拆解可以替代因果分析
