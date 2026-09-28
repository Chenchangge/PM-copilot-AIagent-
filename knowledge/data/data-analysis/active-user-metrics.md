---
id: active-user-metrics
title: DAU、WAU、MAU与活跃用户
category: data-analysis
topic: core-metrics
difficulty: 入门
estimated_minutes: 10
tags:
  - DAU
  - WAU
  - MAU
  - 活跃用户
dependencies:
  - product-metrics-basics
  - metric-definition-and-dimension
---
# DAU、WAU、MAU与活跃用户

## 概述

DAU、WAU、MAU分别描述一定时间窗口内的日、周、月活跃用户规模。

## 定义

DAU（Daily Active Users）通常指某一天内符合活跃定义的去重用户数；WAU和MAU分别扩展到周和月。

## 核心内容

例如：
某产品一天内有：
用户A打开3次
用户B打开1次
用户C打开5次
如果三人都满足活跃定义：
DAU = 3
不是：
3 + 1 + 5 = 9
因为用户数通常需要去重。
活跃定义必须明确。
例如：
登录
打开App
完成核心行为
产生有效内容消费
不同定义会导致不同DAU。

## 常见场景

- 内容产品
- 社交产品
- 工具产品
- SaaS
- 用户活跃分析

## 产品经理关注点

- 理解DAU最重要的是理解“什么行为被定义为活跃”。

## 常见误区

- DAU就是每天打开App的人
- DAU等于访问次数
- DAU越高产品一定越健康
- DAU可以脱离业务目标单独解释
