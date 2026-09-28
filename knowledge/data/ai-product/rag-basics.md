---
id: rag-basics
title: RAG基本原理
category: ai-product
topic: rag-retrieval
difficulty: 基础
estimated_minutes: 20
tags:
  - RAG
  - 检索增强生成
  - LLM
  - 知识库
dependencies:
  - llm-basics
  - token-and-context
  - ai-hallucination
---
# RAG基本原理

## 概述

RAG通过先从外部知识源检索相关信息，再将检索结果提供给LLM生成答案，使模型能够利用模型参数之外的外部知识。

## 定义

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与生成模型结合的技术架构。

## 核心内容

典型RAG流程：
用户问题
↓
Query处理
↓
Embedding
↓
向量/混合检索
↓
Top-K相关内容
↓
Context组装
↓
LLM
↓
答案 + 来源
与直接调用LLM相比，RAG可以让系统：
使用私有知识
使用较新的外部信息
提供来源
降低部分知识型幻觉
不必因为新增知识而重新训练模型
但RAG并不能保证答案正确。
最终效果取决于：
数据质量 × 切分质量 × 检索质量 × 上下文构造 × 模型能力 × Prompt × 评测。

## 常见场景

- 企业知识库
- 产品知识助手
- 内部问答
- 客服
- 文档问答
- AI学习助手

## 产品经理关注点

- 产品经理需要把RAG理解成完整产品链路，而不是“接一个向量数据库”。

## 常见误区

- RAG就是向量数据库
- 有RAG就不会幻觉
- RAG一定比直接问LLM准确
- 所有AI问答都需要RAG
