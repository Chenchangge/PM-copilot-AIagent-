---
id: rag-source-citation
title: RAG来源引用与可追溯性
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 20
tags:
  - 引用
  - Source
  - Citation
  - 可追溯性
  - RAG
dependencies:
  - rag-basics
  - retrieval
  - ai-hallucination
---
# RAG来源引用与可追溯性

## 概述

RAG产品可以将答案与检索证据建立关联，为用户提供来源，提高答案可追溯性，但引用存在不完整和误用风险。

## 定义

来源引用是将模型回答与产生该回答所依据的文档、Chunk或外部来源建立可追踪关系。

## 核心内容

来源信息可以包含：
文档名称
文档版本
来源URL
作者
发布时间
Chunk
页码
引用片段
好的引用机制需要回答：
“这个答案依据了什么？”
更进一步需要判断：
“引用是否真的支持这句话？”
因此：
有引用 ≠ 有效引用。
需要区分：
Source Retrieval
Citation Generation
Citation Verification

## 常见场景

- 企业知识库
- AI搜索
- AI学习助手
- 专业知识问答

## 产品经理关注点

- 引用不仅是UI功能，也属于AI可靠性机制。

## 常见误区

- 有引用就一定正确
- 来源越多越好
- 展示URL就是完成引用
- 模型可以自由生成引用
