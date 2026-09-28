---
id: human-evaluation
title: 人工评测与专家评审
category: ai-product
topic: eval-reliability
difficulty: 基础
estimated_minutes: 20
tags:
  - Human Evaluation
  - 人工评测
  - 专家评测
  - AI评测
dependencies:
  - ai-evaluation
  - ai-evaluation-objective
---
# 人工评测与专家评审

## 概述

人工评测仍然是AI质量评估的重要组成部分，尤其适合复杂、主观或高风险任务。

## 定义

人工评测是由真实用户、领域专家或训练过的评审人员按照统一标准评价AI输出质量的方法。

## 核心内容

人工评测应尽量做到：
明确Rubric
统一评分标准
评审培训
随机抽样
隐藏模型身份
记录评审理由
计算评审一致性
适合人工评测的情况：
专业领域判断
高风险场景
复杂推理
风格评价
用户体验
自动指标难以覆盖的任务
人工评测成本高，因此可以采用：
自动评测
+
LLM Judge
+
人工抽样

## 常见场景

- 医疗类AI
- 法律类AI
- AI教育
- AI写作
- 企业AI

## 产品经理关注点

- 人工评测不是“找几个人随便看看”，而需要设计标准化评测流程。

## 常见误区

- 人工评测一定客观
- 找一个专家就够
- 评审人数越多越好
- 人工评测可以替代所有自动评测
