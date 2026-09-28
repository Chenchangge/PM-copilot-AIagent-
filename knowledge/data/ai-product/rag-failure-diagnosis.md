---
id: rag-failure-diagnosis
title: RAG常见失败模式与问题定位
category: ai-product
topic: rag-retrieval
difficulty: 高级
estimated_minutes: 25
tags:
  - RAG
  - 故障诊断
  - Retrieval
  - Hallucination
dependencies:
  - rag-evaluation
  - context-construction-for-rag
  - rag-source-citation
---
# RAG常见失败模式与问题定位

## 概述

RAG回答错误时，需要按照数据、解析、切分、Embedding、检索、Context、Prompt和LLM逐层定位，而不是直接归因于模型。

## 定义

RAG故障诊断是根据错误答案反向定位RAG链路具体问题的过程。

## 核心内容

可以使用以下排查链：
答案错误
↓
知识源是否正确？
↓
文档是否完整解析？
↓
Chunk是否合理？
↓
Embedding是否正常？
↓
正确Chunk是否被召回？
↓
Top-K是否合理？
↓
Context是否包含正确证据？
↓
Prompt是否要求基于证据回答？
↓
LLM是否正确使用证据？
常见情况：

## 常见场景

- 企业知识库
- AI学习助手
- 技术文档问答

## 产品经理关注点

- 产品经理需要能够从“答案错误”进一步拆解到具体链路。

## 常见误区

- RAG回答错误就是模型问题
- 更换更大模型可以解决所有问题
- 增加Top-K可以解决检索问题
- Prompt可以修复错误知识
