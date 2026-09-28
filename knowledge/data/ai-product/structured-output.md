---
id: structured-output
title: LLM结构化输出
category: ai-product
topic: prompt-agent
difficulty: 进阶
estimated_minutes: 20
tags:
  - Structured Output
  - JSON
  - LLM
  - AI工程
  - 数据结构
dependencies:
  - llm-basics
  - prompt-engineering
---
# LLM结构化输出

## 概述

结构化输出让模型按照预定义的数据结构返回结果，便于后端程序验证、处理和驱动业务逻辑。

## 定义

结构化输出是要求模型生成符合预定义Schema的数据，而不是任意自然语言文本。

## 核心内容

例如AI面试评价可以要求：
{
"score": 78,
"strengths": [
"需求分析较完整"
],
"weaknesses": [
"缺少指标设计"
],
"knowledge_ids": [
"product-metrics-basics"
]
}
与纯文本相比，结构化输出可以让程序：
校验字段
计算分数
保存数据库
生成推荐
驱动下一步流程
但需要注意：
“符合JSON格式”不等于“内容正确”。
因此还需要：
Schema验证
枚举验证
数值范围验证
业务规则验证
引用关系验证

## 常见场景

- AI评价
- AI分类
- AI提取
- Agent
- AI工作流

## 产品经理关注点

- 结构化输出是把LLM从“聊天工具”变成“业务组件”的重要方式之一。

## 常见误区

- JSON合法就代表结果可靠
- Schema可以保证语义正确
- 所有AI任务都应该结构化
- 结构化输出不需要重试
