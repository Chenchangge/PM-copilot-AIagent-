---
id: evaluation-rubric
title: AI评测Rubric设计
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 20
tags:
  - Rubric
  - 评分标准
  - AI评测
dependencies:
  - ai-evaluation
  - ai-evaluation-objective
---
# AI评测Rubric设计

## 概述

Rubric将“什么叫好答案”转化成明确的评分标准，是AI评测可重复性的核心。

## 定义

Rubric是对AI输出质量进行评价时使用的维度、标准、等级和扣分条件。

## 核心内容

一个Rubric可以包括：
Dimension
+
Criteria
+
Score Level
+
Failure Condition
+
Evidence Requirement
例如AI产品面试：
产品思维：
0分：
没有明确用户问题
1分：
能够描述用户，但缺少场景
2分：
能够分析需求和方案
3分：
能够建立完整的目标、场景、方案和取舍
好的Rubric应该：
可理解
可执行
可重复
能区分不同质量水平

## 常见场景

- AI面试
- AI客服
- RAG
- AI写作

## 产品经理关注点

- Rubric应该服务于产品目标，而不是为了评分而评分。

## 常见误区

- Rubric越复杂越好
- 只定义优秀答案
- 没有失败条件
- 评分等级没有明确差异
