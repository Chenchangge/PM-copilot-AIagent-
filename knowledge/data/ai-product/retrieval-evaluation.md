---
id: retrieval-evaluation
title: RAG检索质量评测
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 25
tags:
  - RAG
  - Retrieval
  - 检索评测
  - Recall
dependencies:
  - rag-basics
  - ai-evaluation
---
# RAG检索质量评测

## 概述

RAG系统必须分别评估“有没有找到正确知识”和“模型有没有正确使用知识”，不能把检索和生成混为一个问题。

## 定义

RAG检索评测是对系统是否能够从知识库中找到与用户问题相关、足够完整的信息进行测试。

## 核心内容

例如：
用户问题
↓
Retriever
↓
Top-K chunks
↓
LLM
如果最终回答错误，需要判断：
检索错？
还是
生成错？
可以关注：
Recall
Precision
Hit Rate
Top-K覆盖率
Context Relevance
例如：
正确知识在Top-5中出现。
可以认为该问题至少在检索层获得了较好的覆盖。
但：
正确知识被检索出来 ≠ 最终回答一定正确。

## 常见场景

- 知识库问答
- 企业知识库
- AI搜索

## 产品经理关注点

- RAG评测最好拆成：
- Retrieval Evaluation + Generation Evaluation。

## 常见误区

- 最终答案错误一定是RAG检索错误
- Top-K越大越好
- Recall高就代表最终产品好
- 只看最终答案无法定位问题
