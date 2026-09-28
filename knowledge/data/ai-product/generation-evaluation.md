---
id: generation-evaluation
title: LLM生成质量评测
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 20
tags:
  - LLM
  - Generation
  - 生成质量
  - AI评测
dependencies:
  - ai-evaluation
  - ai-evaluation-metrics
---
# LLM生成质量评测

## 概述

生成评测关注模型在已有输入、上下文和约束下生成的最终答案是否满足任务要求。

## 定义

Generation Evaluation是对模型最终输出在正确性、相关性、完整性、表达质量、依据性等方面进行评估。

## 核心内容

对于RAG：
Retrieval正确
+
Context正确
+
Answer正确
仍然可能出现：
模型误读Context
模型遗漏关键内容
模型加入不存在的信息
模型没有遵循输出格式
因此生成评测需要独立测试。
可以使用：
Rule-based
Exact Match
Semantic Similarity
Human Evaluation
LLM-as-Judge
Structured Rubric

## 常见场景

- AI问答
- AI写作
- AI总结
- AI面试

## 产品经理关注点

- 生成质量需要和具体任务绑定，而不是单纯判断“语言是否自然”。

## 常见误区

- 语言流畅等于质量高
- LLM Judge就是绝对正确
- 只要答案包含关键词就正确
- 模型输出不能使用规则测试
