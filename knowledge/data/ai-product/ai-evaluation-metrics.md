---
id: ai-evaluation-metrics
title: AI产品核心评测指标
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 25
tags:
  - AI评测
  - 指标
  - Quality Metrics
dependencies:
  - ai-evaluation
  - ai-evaluation-objective
---
# AI产品核心评测指标

## 概述

不同AI产品需要采用不同评测指标，但通常可以从正确性、相关性、完整性、依据性、安全性、稳定性、成本和延迟等维度建立指标体系。

## 定义

AI评测指标是对AI输出质量或系统行为进行量化描述的标准。

## 核心内容

常见指标：
Correctness
答案是否正确。
Relevance
答案是否回答了用户问题。
Completeness
是否覆盖关键内容。
Groundedness
答案是否有输入上下文或知识依据。
Faithfulness
生成内容是否忠实于提供的信息。
Citation quality
引用是否真正支持答案。
Safety
是否产生不安全输出。
Consistency
相同或相似输入下表现是否稳定。
Latency
响应时间。
Cost
单次任务或单位用户任务成本。
对于不同产品：
RAG：
Correctness + Groundedness + Citation
AI客服：
Resolution + Correctness + Safety + Latency
AI Agent：
Task Success + Tool Accuracy + Cost + Safety
AI写作：
Relevance + Quality + Style + User Satisfaction

## 常见场景

- RAG
- Agent
- AI客服
- AI写作

## 产品经理关注点

- 不要为了得到一个总分而忽略不同质量维度。

## 常见误区

- 一个Accuracy可以评价所有AI产品
- 只看模型Benchmark
- 用户满意度可以替代技术评测
- 成本与质量无关
