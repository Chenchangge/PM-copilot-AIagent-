---
id: rag-use-case-selection
title: RAG适用场景与不适用场景
category: ai-product
topic: rag-retrieval
difficulty: 基础
estimated_minutes: 15
tags:
  - RAG
  - 场景判断
  - 知识库
  - LLM
dependencies:
  - rag-basics
  - ai-product-value
---
# RAG适用场景与不适用场景

## 概述

RAG更适合需要访问外部知识、私有知识或动态知识的任务，而不是所有LLM任务都应该使用RAG。

## 定义

RAG适用性判断是分析一个AI任务是否需要通过外部检索为模型提供额外知识的过程。

## 核心内容

适合RAG的典型场景：
企业内部知识问答
产品文档问答
政策/制度查询
长文档问答
私有资料问答
需要来源引用的知识问答
不一定需要RAG：
创意写作
普通闲聊
简单文本改写
已经具备足够能力的通用知识任务
不需要外部事实依据的任务
判断标准：
如果核心问题是“模型不知道这个信息”，RAG可能有价值。
如果核心问题是：
“模型不会完成这个任务”，
单纯增加知识不一定能解决。

## 常见场景

- 企业知识库
- AI学习助手
- AI客服
- AI搜索

## 产品经理关注点

- 先判断问题类型，再决定是否引入RAG。

## 常见误区

- AI知识库必须使用RAG
- RAG是所有AI问答的标准答案
- 增加文档就能解决推理问题
- RAG能替代模型能力
