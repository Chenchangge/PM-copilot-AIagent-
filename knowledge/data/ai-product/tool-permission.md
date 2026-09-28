---
id: tool-permission
title: Agent工具权限与安全边界
category: ai-product
topic: prompt-agent
difficulty: 高级
estimated_minutes: 25
tags:
  - Agent安全
  - Tool权限
  - 权限控制
  - Security
dependencies:
  - function-calling
  - enterprise-ai-permission
  - ai-human-in-the-loop
---
# Agent工具权限与安全边界

## 概述

Agent一旦拥有执行工具，就可能从“生成内容”变成“改变真实系统状态”，因此必须建立明确的权限边界。

## 定义

Tool权限是对Agent可调用工具、可操作数据、可执行动作及其参数范围进行限制的安全机制。

## 核心内容

应该区分：
只读工具
例如：
查询订单
查询知识库
查询数据
风险相对较低。
写入工具
例如：
修改订单
创建任务
修改数据库
风险更高。
高风险工具
例如：
转账
删除数据
修改权限
发送外部消息
需要更严格的控制。
权限控制应该考虑：
用户身份
Agent身份
Tool权限
数据范围
参数限制
操作审批
审计
回滚
核心原则：
Tool权限必须由系统控制，不能依赖模型自己“遵守规定”。

## 常见场景

- 企业Agent
- 财务Agent
- CRM Agent
- IT运维Agent

## 产品经理关注点

- Agent安全边界应该设计在系统和工具层，而不是只写在Prompt里。

## 常见误区

- Prompt可以实现权限
- Agent只读就没有风险
- 用户授权后Agent可以无限操作
- 有日志就等于安全
