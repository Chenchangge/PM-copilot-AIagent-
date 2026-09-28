---
id: acceptance-criteria
title: 验收标准设计
category: project-collaboration
topic: project-tools
difficulty: 基础
estimated_minutes: 20
tags:
  - Acceptance Criteria
  - 验收
  - 测试
  - 需求
dependencies:
  - requirement-alignment
  - ai-evaluation
---
# 验收标准设计

## 概述

验收标准用于明确一个需求在什么条件下可以认为已经正确完成。

## 定义

验收标准是对功能、业务规则、异常情况和结果要求进行可验证描述的标准。

## 核心内容

好的验收标准应该尽量：
明确
可验证
与需求目标一致
覆盖正常和异常情况
例如：
当用户完成面试后
→
系统生成评价报告
→
报告必须包含5个固定评价维度
→
总分由后端按权重计算
→
证据引用的turn_id必须存在
验收可以分为：

## 常见场景

- AI评价
- RAG
- Web功能
- B端系统

## 产品经理关注点

- AI产品尤其需要避免：
- “模型给出了答案，所以功能完成”。
- 应该定义AI输出的：
- 结构
- 质量
- 边界
- 失败处理
- 安全要求

## 常见误区

- 测试通过就是全部验收
- 验收标准只针对前端页面
- AI输出无法定义验收标准
- 验收标准应该在开发完成后再写
