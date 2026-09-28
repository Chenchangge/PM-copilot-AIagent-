---
id: rule-engine
title: 规则引擎
category: strategy-product
topic: strategy-basics
difficulty: 进阶
estimated_minutes: 20
tags:
  - 规则引擎
  - Rule Engine
  - 条件
  - 动作
  - 策略配置
dependencies:
  - rule-based-strategy
  - strategy-objective-and-constraints
---
# 规则引擎

## 概述

规则引擎将业务决策规则从具体业务代码中抽离，使策略可以被配置、管理、测试和发布。

## 定义

规则引擎是一种按照规则条件进行判断并输出相应动作或结果的系统能力。

## 核心内容

典型结构：
输入数据
→ 规则匹配
→ 条件判断
→ 优先级处理
→ 输出动作
例如：
用户等级 = VIP
且近30天消费 > X
→ 发放权益A
规则引擎通常需要考虑：
规则创建
编辑
启停
优先级
冲突
版本
灰度
回滚
日志
审计
策略产品经理需要重点关注：
谁配置、谁审核、谁发布、谁回滚、出了问题如何追踪。

## 常见场景

- 风控
- 营销
- 权限
- 审核
- 用户策略
- B端业务系统

## 产品经理关注点

- 规则引擎不仅是“条件配置页面”，还涉及完整策略生命周期。

## 常见误区

- 规则引擎只是if-else可视化
- 不需要版本管理
- 不需要权限
- 规则冲突可以交给开发解决
