---
id: ai-evaluation-objective
title: AI评测目标设计
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 20
tags:
  - AI评测
  - Evaluation Objective
  - 指标
dependencies:
  - ai-evaluation
  - product-metrics-basics
---
# AI评测目标设计

## 概述

评测之前必须先明确产品目标，否则容易出现“指标很好看，但用户实际问题没有解决”的情况。

## 定义

AI评测目标是将产品价值和用户任务转化为可以验证的质量目标。

## 核心内容

例如一个知识问答产品的目标可能是：
用户提出问题
↓
系统找到相关知识
↓
回答正确
↓
答案与问题相关
↓
能够追溯来源
因此不能只测试：
BLEU、ROUGE或模型分数。
而应该围绕真实任务定义：
Correctness
Relevance
Groundedness
Completeness
Citation quality
Safety
Latency
Cost
一个好的评测目标应该能够回答：
“这个指标变好以后，用户的任务完成情况是否真的变好？”

## 常见场景

- RAG问答
- AI客服
- AI学习助手
- AI搜索

## 产品经理关注点

- 评测指标应该从用户任务和业务目标倒推，而不是先选一个流行指标。

## 常见误区

- 指标越多越专业
- 所有AI产品都使用相同指标
- 单一总分可以代表所有质量
- 技术指标等于产品价值
