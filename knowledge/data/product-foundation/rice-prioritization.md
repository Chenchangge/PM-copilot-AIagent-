---
id: rice-prioritization
title: RICE 需求优先级模型
category: product-foundation
topic: requirements-value
difficulty: 进阶
estimated_minutes: 20
tags:
  - RICE
  - 优先级
  - 需求排序
  - Reach
  - Impact
  - Confidence
  - Effort
dependencies:
  - requirement-priority
---
# RICE 需求优先级模型

## 概述

RICE 是一种常见的需求优先级评估方法，通过 Reach、Impact、Confidence、Effort 四个因素对候选项目进行比较。

## 定义

RICE：
RICE = Reach × Impact × Confidence ÷ Effort
其中：
Reach：影响人数或用户规模
Impact：单个用户受到的影响程度
Confidence：对前面估计的信心程度
Effort：所需资源投入

## 核心内容

### Reach
回答：
有多少用户会受到影响？
例如一个季度预计影响 10,000 名用户。
### Impact
用于描述对单个用户或目标指标的影响程度。
不同团队可能采用不同量表，例如：
Massive
High
Medium
Low
Minimal
具体数值标准应该由团队建立，而不是机械套用某个固定标准。
### Confidence
用于降低“拍脑袋估算”的影响。
例如：
100%
80%
50%
代表对 Reach / Impact 等估计的信心程度。
### Effort
通常估算团队需要投入的资源，例如：
产品
设计
开发
测试
运营
可以用人月、工程点数或团队自定义单位。

## 常见场景

- 适用于：
- 多个候选需求同时进入版本规划
- 资源有限
- 需要结构化比较需求

## 产品经理关注点

- RICE 最大的价值不是计算公式本身，而是：
- 强迫团队把“影响多少人、价值多大、我们有多确定、需要多少资源”说清楚。

## 常见误区

- RICE 分数高就一定必须做。
- RICE 可以替代产品经理判断。
- 不同团队的 RICE 分数可以直接比较。
- Impact 的数字具有客观科学意义。
