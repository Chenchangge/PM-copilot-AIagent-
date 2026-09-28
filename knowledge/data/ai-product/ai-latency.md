---
id: ai-latency
title: AI产品延迟设计
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 20
tags:
  - 延迟
  - Latency
  - Streaming
  - AI工程
dependencies:
  - ai-inference-basics
  - token-and-context
---
# AI产品延迟设计

## 概述

AI产品延迟不仅影响技术性能，也直接影响用户体验和任务完成率。

## 定义

AI延迟是用户发起请求到系统产生相应结果之间的时间成本。

## 核心内容

可以拆成：
网络请求
+
检索
+
Rerank
+
模型排队
+
模型推理
+
Tool调用
+
后处理
Agent可能进一步：
LLM
→
Tool
→
LLM
→
Tool
→
LLM
因此多步骤Agent通常存在累积延迟。
常见优化方法：
减少无意义Context
降低不必要的Tool调用
并行执行独立任务
缓存
流式输出
更换模型
优化检索
减少Agent步骤

## 常见场景

- AI聊天
- AI搜索
- AI Agent
- AI客服

## 产品经理关注点

- 需要区分：
- Time to First Token
- 与：
- 完整答案时间。
- 用户可能更在意“多久开始得到反馈”，而不是服务器什么时候完全结束。

## 常见误区

- 延迟越低越好
- 流式输出等于实际推理更快
- 只看平均延迟
- Tool调用次数和延迟无关
