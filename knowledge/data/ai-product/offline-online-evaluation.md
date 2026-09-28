---
id: offline-online-evaluation
title: 离线评测与线上评测
category: ai-product
topic: eval-reliability
difficulty: 进阶
estimated_minutes: 25
tags:
  - 离线评测
  - 线上评测
  - Offline Evaluation
  - Online Evaluation
dependencies:
  - ai-evaluation
  - ai-evaluation-dataset
  - task-success-rate
---
# 离线评测与线上评测

## 概述

离线评测适合快速比较方案和发现问题，线上评测反映真实用户环境，两者需要结合使用。

## 定义

离线评测是在预先准备的数据集上测试AI系统；线上评测是在真实用户流量或受控实验环境中观察系统表现。

## 核心内容

离线评测：
优点：
快
成本低
可重复
易比较
缺点：
测试集可能与真实用户不同
难覆盖长尾问题
不一定反映真实业务价值
线上评测：
可以关注：
Task Success
用户满意度
留存
转化
人工转接率
投诉率
成本
延迟
因此：
离线：
“这个方案在测试集上怎么样？”
线上：
“真实用户用了以后怎么样？”

## 常见场景

- AI客服
- AI搜索
- AI学习产品
- AI Agent

## 产品经理关注点

- 不能因为离线指标提升，就直接认为线上业务一定提升。

## 常见误区

- 离线评测通过就可以直接上线
- 线上数据一定比离线准确
- 线上A/B可以替代离线评测
- 用户满意度可以解释所有技术问题
