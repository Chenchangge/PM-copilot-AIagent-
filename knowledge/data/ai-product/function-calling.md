---
id: function-calling
title: Function Calling与工具调用
category: ai-product
topic: prompt-agent
difficulty: 基础
estimated_minutes: 20
tags:
  - Function Calling
  - Tool Calling
  - API
  - Agent
dependencies:
  - agent-basics
  - structured-output
---
# Function Calling与工具调用

## 概述

Function Calling让模型根据任务决定是否调用预定义工具，并以结构化参数向程序提出调用请求。

## 定义

Function Calling是让LLM根据当前任务生成结构化工具调用请求，由外部程序实际执行工具并将结果返回模型的机制。

## 核心内容

典型链路：
用户：
“帮我查询明天上海天气”
↓
LLM判断需要工具
↓
Tool Call
{
"name": "get_weather",
"arguments": {
"city": "上海",
"date": "明天"
}
}
↓
后端执行天气API
↓
Tool Result
↓
LLM生成最终回答
关键区别：
模型提出“调用什么、传什么参数”，程序负责真正执行。
因此不能简单认为：
模型说调用成功 = 工具已经执行。

## 常见场景

- 查询天气
- 查询数据库
- 搜索
- 发邮件
- 创建任务
- 企业系统操作

## 产品经理关注点

- 产品经理需要设计工具边界、参数、权限和错误处理。

## 常见误区

- Function Calling等于模型自己执行API
- 模型可以绕过权限
- Tool Schema不重要
- 工具调用不需要异常处理
