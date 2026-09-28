---
id: feature-decomposition
title: 功能拆解
category: product-design
topic: requirements-doc
difficulty: 基础
estimated_minutes: 15
tags:
  - 功能拆解
  - Feature
  - 功能模块
  - MVP
dependencies:
  - user-scenario-and-task
  - requirement-analysis-framework
---
# 功能拆解

## 概述

功能拆解是把用户目标和产品需求转化为功能模块、子功能和具体交互规则的过程。

## 定义

功能拆解需要回答：
“为了让用户完成目标，产品必须提供哪些能力？”

## 核心内容

可以使用：
目标 → 核心任务 → 功能模块 → 子功能 → 操作 → 规则 → 状态
例如“AI模拟面试”：
目标：完成一次模拟面试
核心任务：
选择面试条件
开始面试
回答问题
接收追问
完成面试
查看评价
根据薄弱点继续学习
对应功能：
面试配置
题目生成
答案提交
动态追问
面试状态管理
AI评价
报告
学习推荐
拆解时需要区分：
用户必须使用的能力
系统内部能力
MVP必须实现的能力
后续增强能力

## 常见场景

- 新产品设计
- MVP设计
- 复杂功能
- AI Agent产品
- SaaS功能设计

## 产品经理关注点

- 避免“想到什么做什么”，而是从用户任务反推功能。

## 常见误区

- 功能越多产品越完整
- 每一个用户需求都必须对应一个功能
- 功能拆解就是列菜单
- MVP只是删掉一半功能
