---
id: data-quality-and-instrumentation
title: 数据质量与埋点
category: data-analysis
topic: data-tools
difficulty: 进阶
estimated_minutes: 15
tags:
  - 埋点
  - 数据质量
  - Event
  - 数据采集
dependencies:
  - metric-definition-and-dimension
---
# 数据质量与埋点

## 概述

产品分析依赖可靠的数据采集，因此产品经理需要理解核心事件、属性、触发条件和数据质量问题。

## 定义

埋点是对用户行为或系统事件进行记录和采集；数据质量是指数据在准确性、完整性、一致性、及时性等方面是否满足分析要求。

## 核心内容

一个事件通常需要定义：
event_name
触发时机
用户ID
时间
页面/功能
事件属性
必填字段
数据类型
例如：
interview_answer_submitted
属性：
session_id
question_id
answer_length
answer_duration
direction
interview_type
需要避免：
同一事件不同端口径不同
重复上报
漏报
事件名称混乱
属性定义不一致
版本升级后埋点失效

## 常见场景

- 产品数据分析
- 漏斗
- 用户行为分析
- AI产品
- A/B实验

## 产品经理关注点

- 没有可靠埋点，后续的数据分析和实验都可能失去基础。

## 常见误区

- 埋点越多越好
- 埋点只是开发工作
- 数据分析时发现没有数据再补埋点即可
- 埋点数据天然准确
