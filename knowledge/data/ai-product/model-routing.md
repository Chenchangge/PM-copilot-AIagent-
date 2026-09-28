---
id: model-routing
title: 模型路由与多模型策略
category: ai-product
topic: ai-engineering
difficulty: 高级
estimated_minutes: 25
tags:
  - Model Routing
  - 多模型
  - 模型路由
  - 成本优化
dependencies:
  - model-selection-for-pm
  - ai-cost
  - ai-evaluation
---
# 模型路由与多模型策略

## 概述

模型路由根据任务类型、复杂度、成本或实时状态动态选择不同模型，使系统不必所有请求都使用同一个模型。

## 定义

模型路由是根据请求特征和系统策略，在多个候选模型之间动态选择模型的机制。

## 核心内容

例如：
简单问题
→
轻量模型
复杂推理
→
高能力模型
结构化抽取
→
专用模型
高风险任务
→
高可靠模型
还可以基于：
用户类型
任务类型
Token长度
历史失败率
当前延迟
服务价格
服务健康状态
进行路由。
进一步可以形成：
Router
↓
Model A / B / C
↓
Evaluation
↓
Fallback

## 常见场景

- AI客服
- AI搜索
- Agent
- 企业AI

## 产品经理关注点

- 模型路由本质是：
- 质量、成本、延迟之间的动态资源分配。

## 常见误区

- 多模型一定比单模型好
- 路由只考虑价格
- 路由不需要评测
- Router错误不会影响最终质量
