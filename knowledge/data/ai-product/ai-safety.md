---
id: ai-safety
title: AI安全与安全护栏
category: ai-product
topic: ai-engineering
difficulty: 进阶
estimated_minutes: 25
tags:
  - AI安全
  - Safety
  - Guardrail
  - 内容安全
dependencies:
  - ai-security
  - tool-permission
  - ai-evaluation
---
# AI安全与安全护栏

## 概述

AI安全护栏通过输入、模型、工具和输出多个层面的控制降低产品产生危险或不符合预期行为的风险。

## 定义

AI Guardrail是围绕AI系统建立的输入限制、输出检测、权限控制、风险识别和人工干预机制。

## 核心内容

可以建立多层护栏：
User Input
↓
Input Guardrail
↓
LLM
↓
Tool Permission
↓
Output Guardrail
↓
Human Review
↓
User
不同场景风险不同。
低风险：
AI生成学习笔记。
高风险：
AI自动修改生产系统数据。
后者需要更强：
权限限制
操作确认
审计
回滚
人工审批

## 常见场景

- AI客服
- Agent
- 企业AI
- AI办公

## 产品经理关注点

- Guardrail应该与风险等级匹配，而不是所有功能使用相同强度的限制。

## 常见误区

- 一个安全模型可以解决所有问题
- Guardrail就是关键词过滤
- 所有AI功能都需要人工审核
- 风险越低越应该增加更多限制
