---
id: metadata-filtering
title: RAG元数据过滤
category: ai-product
topic: rag-retrieval
difficulty: 进阶
estimated_minutes: 20
tags:
  - Metadata
  - 元数据
  - Filter
  - RAG
  - 权限
dependencies:
  - retrieval
  - vector-database
---
# RAG元数据过滤

## 概述

元数据过滤可以在语义检索之前或过程中缩小候选范围，提高检索相关性并支持权限和业务条件。

## 定义

元数据过滤是利用文档的结构化属性限制检索范围的方法。

## 核心内容

例如知识库：
category = AI产品
difficulty = 进阶
source = internal
version = current
用户查询：
RAG进阶知识。
可以先限制：
category = AI产品
再做向量搜索。
企业知识库还可以：
tenant_id
organization_id
permission_level
document_status
重要原则：
权限过滤应该成为检索链路的一部分，而不能只依赖Prompt告诉模型“不要看这些内容”。

## 常见场景

- 企业知识库
- 多租户SaaS
- 产品知识库
- 权限隔离

## 产品经理关注点

- 元数据既服务检索，也服务治理、权限、版本和可解释性。

## 常见误区

- Metadata只是标签
- Prompt可以代替权限控制
- 所有内容都应该进入同一个检索池
- Filter越多越好
