---
id: ai-evaluation-dataset
title: AI评测数据集设计
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 25
tags:
  - AI评测
  - Dataset
  - 测试集
  - Golden Set
dependencies:
  - ai-evaluation
  - ai-evaluation-objective
---
# AI评测数据集设计

## 概述

高质量评测首先依赖高质量测试数据，评测集应该覆盖真实用户场景、难例、边界情况和高风险情况。

## 定义

AI评测数据集是用于系统性测试AI产品质量的一组输入、期望结果、参考答案、标签或评价标准。

## 核心内容

一个评测样本可以包含：
id: eval-001
question: ...
expected_points:
- ...
reference_answer: ...
category: ...
difficulty: ...
risk_level: ...
source: ...
评测集应该覆盖：

## 常见场景

- RAG
- AI客服
- AI面试
- Agent

## 产品经理关注点

- 评测集不是越大越好，更重要的是：
- 是否能够代表真实使用场景。

## 常见误区

- 1000道随机题就一定比100道高质量题好
- 测试集全部由AI生成即可
- 评测集只需要简单问题
- 测试集永远不需要更新
