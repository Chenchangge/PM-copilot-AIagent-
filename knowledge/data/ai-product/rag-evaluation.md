---
id: rag-evaluation
title: RAG评测基础
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 25
tags:
  - RAG评测
  - Evaluation
  - Retrieval
  - Answer Quality
dependencies:
  - rag-basics
  - retrieval
  - ai-evaluation
---
# RAG评测基础

## 概述

RAG评测必须区分检索质量和最终回答质量，否则很难定位问题究竟来自知识库、检索还是生成模型。

## 定义

RAG评测是对RAG系统从数据、检索、上下文到最终答案进行系统测试和比较的过程。

## 核心内容

至少应该区分：

## 常见场景

- RAG版本升级
- Embedding模型更换
- Chunking调整
- Prompt优化
- Rerank加入前后对比

## 产品经理关注点

- 评测必须支持定位问题，而不是只产生一个总分。

## 常见误区

- RAG评测就是让LLM打分
- 只测试最终答案
- Recall高就代表答案一定好
- 100道测试题就能代表所有真实场景
