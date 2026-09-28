---
id: prompt-engineering
title: Prompt工程基础
category: ai-product
topic: prompt-agent
difficulty: 基础
estimated_minutes: 20
tags:
  - Prompt
  - 提示词
  - LLM
  - 指令
  - 输出约束
dependencies:
  - llm-basics
---
# Prompt工程基础

## 概述

Prompt工程通过明确任务、上下文、约束和输出要求，提高模型完成特定任务的稳定性和可控性。

## 定义

Prompt工程是针对模型输入设计任务描述、上下文、示例、约束和输出格式的方法。

## 核心内容

一个结构清晰的Prompt通常可以包含：
角色 / System Context
告诉模型任务背景。
任务
明确需要完成什么。
上下文
提供必要的信息。
约束
规定不能做什么或必须满足什么条件。
输出格式
例如要求JSON。
示例
通过Few-shot示例说明预期行为。
例如：
任务：
判断用户回答是否覆盖指定知识点。
输入：
...
评分标准：
...
输出：
{
"score": 0-100,
"evidence": [],
"missing_points": []
}
Prompt工程的目标不是写“越长越复杂”的Prompt，而是：
降低任务歧义，提高输出一致性和可验证性。

## 常见场景

- AI问答
- AI评价
- AI客服
- 内容生成
- Agent

## 产品经理关注点

- 产品经理需要关注Prompt是否服务于产品任务，而不是追求Prompt技巧本身。

## 常见误区

- Prompt越长越好
- 加一句“你是专家”就能显著提高准确率
- Prompt可以解决所有幻觉
- Prompt不需要评测
