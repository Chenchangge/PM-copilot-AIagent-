---
id: agent-idempotency
title: Agent幂等与重复执行控制
category: ai-product
topic: prompt-agent
difficulty: 高级
estimated_minutes: 20
tags:
  - Agent
  - 幂等
  - Idempotency
  - Tool Calling
dependencies:
  - agent-error-handling
  - agent-state-management
  - function-calling
---
# Agent幂等与重复执行控制

## 概述

Agent重试、网络异常或状态恢复可能导致同一个工具被重复调用，因此具有副作用的Tool必须考虑幂等。

## 定义

幂等是同一个操作执行一次或多次，在业务结果上保持预期一致性的机制。

## 核心内容

例如：
创建订单
发送邮件
扣款
删除数据
这些操作如果因为网络超时被Agent再次执行，可能产生严重后果。
常见机制：
client_request_id
idempotency_key
操作状态记录
唯一约束
事务
执行前检查
例如：
request_id = abc123
第一次：
创建任务成功
第二次：
发现abc123已经执行
→ 返回第一次结果

## 常见场景

- 支付
- 订单
- 企业Agent
- 自动发消息

## 产品经理关注点

- Agent的自动化能力越强，幂等越重要。

## 常见误区

- API成功返回就不会重复
- Retry不会导致重复执行
- 只有支付场景需要幂等
- 幂等只属于后端技术
