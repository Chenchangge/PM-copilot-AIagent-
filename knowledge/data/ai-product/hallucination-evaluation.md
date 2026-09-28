---
id: hallucination-evaluation
title: AI幻觉评测
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 25
tags:
  - 幻觉
  - Hallucination
  - AI评测
  - Groundedness
dependencies:
  - llm-basics
  - rag-basics
  - ai-evaluation
---
# AI幻觉评测

## 概述

AI幻觉评测重点判断模型是否生成了没有足够依据支持的事实、引用或结论。

## 定义

AI幻觉通常指模型生成看似合理但缺乏事实依据、与给定资料不一致或虚构的信息。

## 核心内容

需要区分：

## 常见场景

- RAG
- AI搜索
- AI客服
- AI研究助手

## 产品经理关注点

- 降低幻觉不能只依靠Prompt，需要从：
- 数据
- +
- 检索
- +
- 模型
- +
- Prompt
- +
- 输出验证
- +
- 产品交互
- 多个层面解决。

## 常见误区

- 有RAG就不会幻觉
- Temperature调低就没有幻觉
- 让模型说“我不知道”就解决了幻觉
- 幻觉只属于模型问题
