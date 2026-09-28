---
id: pairwise-evaluation
title: Pairwise评测
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 20
tags:
  - Pairwise
  - A/B
  - 模型比较
  - AI评测
dependencies:
  - ai-evaluation
  - human-evaluation
---
# Pairwise评测

## 概述

Pairwise评测通过让评审比较两个候选输出，而不是分别给绝对分数，适合模型、Prompt或方案之间的相对比较。

## 定义

Pairwise Evaluation是让评测者比较两个或多个候选输出，判断哪个更符合评价标准的方法。

## 核心内容

例如：
Question
Answer A
Answer B
↓
Judge
A更好 / B更好 / 平局
适合比较：
Model A vs Model B
Prompt A vs Prompt B
RAG Top-3 vs Top-5
Workflow A vs Workflow B
优点：
相对判断通常比绝对评分更容易
适合模型方案对比
风险：
位置偏差
输出顺序影响
两个答案都不好但必须选一个
比较标准不明确
可以通过：
随机化A/B顺序
降低部分偏差。

## 常见场景

- 模型选型
- Prompt优化
- RAG方案比较

## 产品经理关注点

- Pairwise适合回答：
- “方案A和方案B哪个更适合这个任务？”
- 而不是：
- “方案A到底有多好？”

## 常见误区

- Pairwise天然客观
- A/B必须二选一
- 两个答案只要一个更好就代表其中一个合格
- Pairwise可以替代所有绝对评测
