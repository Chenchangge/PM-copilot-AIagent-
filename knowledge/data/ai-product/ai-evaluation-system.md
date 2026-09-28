---
id: ai-evaluation-system
title: AI评测体系建设
category: ai-product
topic: eval-reliability
difficulty: 高级
estimated_minutes: 30
tags:
  - AI评测
  - Evaluation System
  - 质量体系
  - AI产品
dependencies:
  - ai-evaluation
  - ai-evaluation-dataset
  - ai-evaluation-metrics
  - regression-evaluation
  - offline-online-evaluation
---
# AI评测体系建设

## 概述

完整AI评测体系应该覆盖数据集、离线评测、自动评测、人工评测、线上监控和回归机制，而不是一个单独的评分脚本。

## 定义

AI评测体系是围绕AI产品生命周期建立的数据、指标、测试、评审和持续监控机制。

## 核心内容

可以形成：
真实用户场景
↓
构建评测集
↓
定义Rubric
↓
离线评测
↓
发现问题
↓
模型 / Prompt / RAG / Tool优化
↓
回归测试
↓
灰度
↓
线上监控
↓
用户反馈
↓
新增评测样本
↓
评测集持续迭代
评测体系至少包含：

## 常见场景

- AI学习助手
- RAG知识库
- AI客服
- Agent
- AI面试

## 产品经理关注点

- AI产品经理需要能够把：
- 用户问题 → 评测指标 → 数据集 → 实验 → 版本迭代
- 串成完整闭环。

## 常见误区

- 建一个评测脚本就是评测体系
- 只有研发需要关注评测
- 评测体系越复杂越好
- 线上指标和模型指标可以完全割裂
