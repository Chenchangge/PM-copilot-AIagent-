---
id: ranking-strategy
title: 排序策略
category: strategy-product
topic: strategy-basics
difficulty: 进阶
estimated_minutes: 20
tags:
  - 排序
  - Ranking
  - 推荐
  - 搜索
dependencies:
  - recommendation-system-basics
  - strategy-objective-and-constraints
---
# 排序策略

## 概述

排序策略决定多个候选对象在产品中的展示顺序。

## 定义

排序策略是根据目标函数、用户特征、内容特征和业务约束，对候选对象进行优先级排序的机制。

## 核心内容

排序可以基于：
相关性
用户偏好
热度
新鲜度
商业价值
内容质量
风险等级
但实际排序通常是多个目标的组合。
例如搜索：
相关性
内容质量
新鲜度
个性化
推荐：
用户兴趣
内容质量
多样性
新鲜度
业务目标
排序策略必须考虑：
权重
冲突
兜底
异常
监控

## 常见场景

- 搜索
- 推荐
- 电商
- 广告
- 内容平台

## 产品经理关注点

- 排序策略的核心是“为什么这个结果排在另一个结果前面”。

## 常见误区

- 排序只看一个分数
- 点击率高就应该排前面
- 排序不需要业务规则
- 排序调整不会影响生态
