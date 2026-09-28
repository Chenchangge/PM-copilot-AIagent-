---
id: regression-evaluation
title: AI回归评测
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 20
tags:
  - 回归测试
  - Regression
  - AI评测
  - CI
dependencies:
  - ai-evaluation-dataset
  - ai-evaluation
  - ai-evaluation-stability
---
# AI回归评测

## 概述

AI产品不断修改Prompt、模型、知识库和代码，因此需要通过固定评测集验证新版本是否导致已有能力退化。

## 定义

AI回归评测是使用固定或版本化测试集，对新版本与旧版本进行比较，以发现已有能力退化的方法。

## 核心内容

可能影响AI质量的变更包括：
模型升级
Prompt修改
Chunk策略修改
Embedding模型修改
Reranker修改
Tool修改
知识库更新
业务规则变化
流程：
旧版本
↓
Golden Set
↓
Baseline
新版本
↓
Golden Set
↓
Compare
↓
是否退化？
需要保留：
测试集版本
模型版本
Prompt版本
知识库版本
评测结果

## 常见场景

- RAG
- AI客服
- AI Agent
- AI面试

## 产品经理关注点

- AI产品迭代必须具备“改了什么 → 质量变化多少”的能力。

## 常见误区

- 新模型一定比旧模型好
- Prompt修改只影响当前功能
- 回归测试只测试代码
- 线上用户反馈可以完全替代回归测试
