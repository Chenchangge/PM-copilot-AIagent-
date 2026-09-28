---
id: conversion-problem-diagnosis
title: 转化下降问题分析
category: data-analysis
topic: analysis-methods
difficulty: 进阶
estimated_minutes: 20
tags:
  - 转化下降
  - 问题定位
  - 指标异常
  - 数据诊断
dependencies:
  - funnel-analysis
  - metric-definition-and-dimension
  - metric-decomposition
---
# 转化下降问题分析

## 概述

面对指标下降，产品经理需要先确认数据是否真实，再通过分维度、分阶段和结合业务变化逐步定位问题。

## 定义

转化问题诊断是从“指标异常”逐步定位到“具体环节、用户群体、版本或业务条件”的分析过程。

## 核心内容

例如注册转化率下降。
第一步：确认数据是否可信
埋点是否改变
指标口径是否改变
数据链路是否异常
第二步：确认时间范围
从什么时候开始
是否突然下降
是否周期性变化
第三步：拆维度
新老用户
渠道
设备
地区
版本
第四步：拆漏斗
进入注册页
开始填写
提交
验证
完成
第五步：结合外部变化
产品改版
活动变化
价格变化
技术故障
流量结构变化
第六步：提出假设并验证。

## 常见场景

- 转化下降
- DAU下降
- 付费下降
- 留存下降
- AI功能使用下降

## 产品经理关注点

- 不要从一个数字直接跳到结论。

## 常见误区

- 找到相关性就等于找到原因
- 指标异常一定是产品问题
- 数据分析只需要看Dashboard
- 最大下降维度就是根因
