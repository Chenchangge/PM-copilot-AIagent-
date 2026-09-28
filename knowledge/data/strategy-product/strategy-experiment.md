---
id: strategy-experiment
title: 策略实验与灰度发布
category: strategy-product
topic: strategy-basics
difficulty: 进阶
estimated_minutes: 20
tags:
  - 策略实验
  - A/B测试
  - 灰度
  - 实验
dependencies:
  - strategy-objective-and-constraints
  - growth-experiment
  - ab-testing-basics
---
# 策略实验与灰度发布

## 概述

策略实验通过小规模验证和对照分析判断策略调整是否带来预期效果。

## 定义

策略实验是针对策略变化建立实验组和对照组，并通过指标判断策略效果的过程。

## 核心内容

策略实验通常包括：
明确目标
建立假设
确定实验对象
选择主指标
设置护栏指标
随机分组或其他合理实验设计
灰度
分析结果
决定扩大、回滚或继续实验
策略实验特别需要关注：
样本污染
实验组之间相互影响
长期效果
用户结构变化
指标波动

## 常见场景

- 推荐
- 搜索
- 用户增长
- 商业化
- AI产品

## 产品经理关注点

- 策略实验不是单纯比较一个数字，而是判断策略变化是否真正带来目标改善且没有产生不可接受的副作用。

## 常见误区

- 指标涨了就一定可以全量
- 灰度等于A/B测试
- 实验时间越长越好
- 只看主指标即可
