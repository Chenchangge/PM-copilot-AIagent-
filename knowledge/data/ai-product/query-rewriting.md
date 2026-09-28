---
id: query-rewriting
title: RAG Query改写
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 20
tags:
  - Query Rewrite
  - 查询改写
  - RAG
  - 搜索
dependencies:
  - retrieval
  - llm-basics
---
# RAG Query改写

## 概述

用户问题不一定天然适合检索，Query改写可以补充上下文、消除歧义或转换为更适合搜索的表达。

## 定义

Query改写是对用户原始问题进行重写、扩展或拆分，使其更适合后续检索的过程。

## 核心内容

例如用户连续对话：
用户：什么是RAG？
用户：它为什么会出现幻觉？
第二句话本身信息不足。
系统可以改写为：
“RAG为什么仍然可能产生AI幻觉？”
常见方法：
补充对话上下文
同义词扩展
Query重写
Query拆分
多Query检索
但Query改写本身也可能产生错误。
因此需要：
原Query保留 + 改写结果可追踪 + 失败回退。

## 常见场景

- 多轮知识问答
- 企业搜索
- 文档问答
- AI搜索

## 产品经理关注点

- 检索问题不一定出在知识库，也可能出在用户Query和检索Query之间。

## 常见误区

- 所有Query都应该改写
- 改写越复杂越好
- 改写不会改变用户原意
- Query改写可以替代检索优化
