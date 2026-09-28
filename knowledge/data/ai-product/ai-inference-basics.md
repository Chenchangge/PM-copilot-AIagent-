---
id: ai-inference-basics
title: AI推理基础
category: ai-product
topic: ai-engineering
difficulty: 基础
estimated_minutes: 20
tags:
  - AI推理
  - Inference
  - LLM
  - AI工程
dependencies:
  - llm-basics
  - token-and-context
---
# AI推理基础

## 概述

AI推理是已经训练完成的模型接收输入并生成预测或输出的过程，是AI产品运行成本和性能的重要基础。

## 定义

Inference是使用已经训练好的模型处理用户输入并产生输出的过程。

## 核心内容

对于LLM产品，可以简化为：
用户输入
↓
Prompt + Context
↓
模型Inference
↓
Token生成
↓
输出
推理过程通常会受到以下因素影响：
输入Token数量
输出Token数量
模型大小
模型架构
推理参数
并发量
硬件
服务商
网络
缓存
产品经理需要理解：
模型能力、成本和延迟并不是完全独立的。
例如：
更大模型
→
通常能力更强
→
可能成本更高
→
可能延迟更高
但具体结果取决于模型、任务、部署方式和服务商。

## 常见场景

- AI问答
- AI客服
- AI Agent
- AI搜索

## 产品经理关注点

- PM不需要成为模型推理工程师，但需要能够理解影响成本和性能的主要变量。

## 常见误区

- 模型调用就是简单API请求
- 模型越大一定越适合产品
- Token只影响价格
- 推理速度完全由模型决定
