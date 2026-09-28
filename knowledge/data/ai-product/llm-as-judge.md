---
id: llm-as-judge
title: LLM-as-a-Judge
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 25
tags:
  - LLM-as-a-Judge
  - AI评测
  - 自动评测
  - Rubric
dependencies:
  - ai-evaluation
  - ai-evaluation-metrics
---
# LLM-as-a-Judge

## 概述

LLM-as-a-Judge利用另一个模型按照预先定义的评价标准对AI输出进行评分或比较，可以降低人工评测成本，但必须控制偏差。

## 定义

LLM-as-a-Judge是使用LLM作为评审器，根据指定Rubric对目标模型输出进行评价的方法。

## 核心内容

基本结构：
Question
+
Reference
+
Candidate Answer
+
Rubric
↓
Judge LLM
↓
Score
+
Reason
Rubric应该明确：
评分维度
得分标准
必须满足的条件
严重错误
评分范围
例如：
0分：完全错误
1分：包含少量相关信息
2分：基本正确但遗漏关键点
3分：正确且完整
但Judge本身可能存在：
Position bias
Verbosity bias
Self-preference
判断不稳定
对复杂事实判断错误
因此最好：
LLM Judge + 人工抽样校验。

## 常见场景

- 大规模问答评测
- AI客服
- RAG
- AI写作

## 产品经理关注点

- Judge不是“自动真理机器”，而是一种评测工具。

## 常见误区

- Judge分数就是客观真值
- Judge模型越大一定越可靠
- 不需要人工校验
- 只提供一个总分就够了
