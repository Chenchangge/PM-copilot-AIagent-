---
id: strategy-versioning
title: 策略版本管理
category: strategy-product
topic: strategy-basics
difficulty: 进阶
estimated_minutes: 15
tags:
  - 策略版本
  - Version
  - 灰度
  - 回滚
dependencies:
  - rule-engine
  - strategy-experiment
---
# 策略版本管理

## 概述

策略版本管理保证策略变更可追踪、可比较、可回滚。

## 定义

策略版本管理是对不同策略配置、规则或模型组合进行版本记录和生命周期管理的机制。

## 核心内容

一个策略版本至少需要记录：
版本号
修改人
修改时间
修改内容
生效范围
生效时间
实验ID
指标表现
回滚方式
典型流程：
草稿
→ 测试
→ 小流量
→ 灰度
→ 全量
→ 监控
→ 回滚/下线

## 常见场景

- 推荐
- 风控
- 营销
- AI策略
- B端策略平台

## 产品经理关注点

- 策略上线后的可追踪性和可回滚性与策略本身同样重要。

## 常见误区

- 策略配置不需要版本
- 出问题重新改一次就行
- 只有代码需要版本管理
- 灰度之后不需要记录实验结果
