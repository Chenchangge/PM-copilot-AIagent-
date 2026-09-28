---
id: ai-evaluation
title: AI产品评测基础
category: ai-product
topic: eval-reliability
difficulty: 基础
estimated_minutes: 20
tags:
  - AI评测
  - Evaluation
  - LLM
  - AI产品
dependencies:
  - llm-basics
  - product-metrics-basics
---
# AI产品评测基础

## 概述

AI评测是通过预先定义的数据集、指标和测试方法，系统判断AI产品是否满足质量目标的过程。

## 定义

AI评测是对模型或AI应用在准确性、相关性、稳定性、安全性、成本、延迟等方面进行系统测试和衡量的过程。

## 核心内容

AI评测与传统软件测试存在明显差异。
传统软件：
输入A
→
确定输出B
→
Pass / Fail
生成式AI：
输入
→
模型
→
可能存在多个合理答案
因此需要定义：
测试集
评测目标
评测指标
评分标准
评测方法
阈值
失败案例
回归机制
AI评测至少应该回答：
AI到底好不好？
进一步回答：
好在哪里？
差在哪里？
改动之后有没有变好？

## 常见场景

- AI问答
- RAG
- AI客服
- AI写作
- AI Agent
- AI面试

## 产品经理关注点

- 产品经理不能只依赖“感觉回答不错”，而需要建立可重复的评测方法。

## 常见误区

- 模型排行榜可以直接代表产品质量
- 用户觉得好就是评测
- LLM输出无法评测
- 只测准确率就够了
