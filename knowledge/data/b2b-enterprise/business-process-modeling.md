---
id: business-process-modeling
title: 企业业务流程建模
category: b2b-enterprise
topic: b2b-basics
difficulty: 基础
estimated_minutes: 20
tags:
  - 业务流程
  - 流程建模
  - BPM
  - ToB
dependencies:
  - b2b-product-basics
  - requirement-analysis-framework
---
# 企业业务流程建模

## 概述

B端产品通常是对现实业务流程进行数字化，因此理解业务流程是B端产品设计的重要基础。

## 定义

业务流程建模是将现实业务中的角色、活动、条件、输入、输出和状态变化结构化表达的过程。

## 核心内容

分析一个企业流程时，可以按照：
触发 → 角色 → 操作 → 判断 → 状态变化 → 下一步 → 完成
例如请假流程：
员工提交申请
→ 部门主管审批
→ HR备案
→ 假期余额变化
→ 流程结束。
复杂流程还需要考虑：
并行
条件分支
驳回
撤回
转交
超时
自动处理
异常
产品设计不能只画“主流程”。

## 常见场景

- OA
- 审批
- CRM
- ERP
- 财务
- 企业AI工作流

## 产品经理关注点

- 产品经理应该先理解业务流程，再决定系统功能。

## 常见误区

- 流程图就是产品设计
- 只需要画正常流程
- 所有流程都应该标准化
- 业务方说的流程就是完整流程
