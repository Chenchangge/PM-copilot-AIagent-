---
id: enterprise-ai-permission
title: 企业AI中的权限与数据隔离
category: b2b-enterprise
topic: b2b-basics
difficulty: 高级
estimated_minutes: 25
tags:
  - 企业AI
  - 数据隔离
  - 权限
  - RAG
  - Agent
dependencies:
  - enterprise-ai-product
  - enterprise-permission-model
  - data-permission
---
# 企业AI中的权限与数据隔离

## 概述

企业AI不能因为拥有检索或工具调用能力，就绕过企业原有的数据权限。

## 定义

企业AI权限控制是确保AI只能访问当前用户或当前组织被授权访问的数据、工具和业务操作范围。

## 核心内容

假设企业知识库中存在：
A部门资料
B部门资料
财务资料
HR资料
用户只能访问A部门资料。
AI进行RAG时不能：
先检索全部文档，再依靠Prompt告诉模型不要回答。
更合理的设计应该尽可能在检索、数据访问和工具调用层建立权限边界。
典型链路：
用户身份
→ 组织 / 角色
→ 权限判断
→ 可访问数据范围
→ 检索
→ LLM
→ 输出
Agent还需要控制：
用户能调用哪些工具，以及工具允许执行什么操作。
例如：
查询CRM：
可能允许。
修改客户状态：
需要更高权限或人工确认。
删除数据：
可能禁止AI直接执行。

## 常见场景

- 企业RAG
- 企业Agent
- 企业Copilot
- CRM AI
- 数据分析AI

## 产品经理关注点

- 企业AI权限必须同时覆盖：
- 知识访问 + 工具调用 + 数据操作。

## 常见误区

- Prompt中的“不要泄露数据”就是权限控制
- RAG天然安全
- AI不能访问数据库就没有权限问题
- 只有管理员需要权限
