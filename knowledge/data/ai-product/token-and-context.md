---
id: token-and-context
title: Token、上下文窗口与上下文管理
category: ai-product
topic: llm-basics
difficulty: 基础
estimated_minutes: 20
tags:
  - Token
  - Context Window
  - 上下文
  - 成本
  - LLM
dependencies:
  - llm-basics
---
# Token、上下文窗口与上下文管理

## 概述

Token影响模型输入输出的处理规模和成本，上下文窗口决定一次请求能够处理多少上下文信息。

## 定义

Token是模型处理文本时使用的离散单位；上下文窗口是模型在一次处理过程中能够考虑的输入、历史信息以及相关输出范围。

## 核心内容

一个AI问答系统可能将以下内容发送给模型：
System Prompt
用户问题
历史对话
RAG检索结果
工具结果
输出要求
这些内容共同消耗上下文空间。
因此：
上下文管理 = 选择真正有价值的信息进入模型。
常见策略：
历史消息截断
对话摘要
RAG检索
Top-K控制
文档分块
上下文压缩
去除重复信息
Token还会影响：
API成本
首Token延迟
总生成时间
上下文可用空间

## 常见场景

- AI聊天
- RAG
- 长文档问答
- Agent

## 产品经理关注点

- 不是“塞更多内容给模型”就更好，而是让模型获得足够且相关的上下文。

## 常见误区

- Token等于汉字
- 上下文越大一定越好
- 历史对话全部保留最好
- RAG结果越多越准确
