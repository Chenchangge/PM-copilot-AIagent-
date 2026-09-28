---
id: ab-testing-basics
title: A/B测试基础
category: data-analysis
topic: experimentation
difficulty: 进阶
estimated_minutes: 20
tags:
  - A/B测试
  - 实验
  - Experiment
  - 对照组
dependencies:
  - product-metrics-basics
  - metric-definition-and-dimension
---
# A/B测试基础

## 概述

A/B测试通过将用户随机分配到不同实验组，在尽量控制其他条件的情况下比较不同方案的指标表现。

## 定义

A/B测试是一种在线受控实验方法，用于评估不同产品方案对目标指标的影响。

## 核心内容

基本结构：
控制组 A → 原方案
实验组 B → 新方案
核心过程：
明确假设
确定实验对象
确定实验变量
随机分组
确定核心指标
确定护栏指标
运行实验
分析结果
判断是否支持假设
例如：
假设：
“简化注册流程可以提高注册完成率。”
实验：
A：原注册流程
B：简化后的注册流程
需要同时关注：
注册完成率
后续留存
异常率
业务质量

## 常见场景

- 页面改版
- 推荐策略
- 注册流程
- 价格实验
- AI提示词实验

## 产品经理关注点

- A/B测试解决的是“方案是否产生了可观察差异”，不是自动证明所有业务原因。

## 常见误区

- A/B测试只要两组数据就可以
- 实验组数据更高就一定成功
- A/B测试可以验证任何问题
- 实验周期越长越好
