// 当前阶段使用 Mock 数据占位，后续替换为后端 API 返回。

export const mockProfile = {
  name: '求职者',
  targetRole: '产品经理',
  level: '校招 / 初级',
}

export const mockStats = {
  learnedCount: 12, // 已学习知识点
  completedPlans: 2, // 完成学习计划
  interviewCount: 3, // 完成模拟面试
}

// ---- 首页 ----
export const continueLearning = [
  { id: 2, title: '从需求到产品方案与 MVP', progress: 60 },
  { id: 7, title: 'RAG 检索增强生成入门', progress: 20 },
  { id: 3, title: '产品指标与漏斗分析', progress: 45 },
]

// ---- 知识库 ----
export const knowledgeCategories = ['产品基础', '产品设计', '数据分析', 'AI产品', '工具', '产品经理面试']

export const knowledgeList = [
  { id: 1, category: '产品基础', title: '产品经理的核心职责', summary: '理解 PM 在团队中的定位与日常工作。', readMinutes: 6, updatedAt: '2026-09-12', status: '已完成' },
  { id: 2, category: '产品设计', title: '从需求到产品方案与 MVP', summary: '需求分析、方案设计与 MVP 验证。', readMinutes: 9, updatedAt: '2026-09-10', status: '进行中' },
  { id: 3, category: '数据分析', title: '产品指标与漏斗分析', summary: '北极星指标、留存转化与漏斗拆解。', readMinutes: 8, updatedAt: '2026-09-08', status: '未开始' },
  { id: 4, category: 'AI产品', title: 'AI 产品经理入门', summary: '大模型能力边界与 AI 产品设计。', readMinutes: 10, updatedAt: '2026-09-05', status: '未开始' },
  { id: 5, category: '工具', title: '常用产品工具一览', summary: '原型、文档、项目管理与协作工具。', readMinutes: 5, updatedAt: '2026-09-03', status: '已完成' },
  { id: 6, category: '产品经理面试', title: 'PM 面试高频问题与回答思路', summary: '自我介绍、项目复盘与开放题框架。', readMinutes: 12, updatedAt: '2026-09-01', status: '进行中' },
  { id: 7, category: 'AI产品', title: 'RAG 检索增强生成入门', summary: 'RAG 的原理、流程与在 AI 产品中的价值。', readMinutes: 11, updatedAt: '2026-08-28', status: '未开始' },
  { id: 8, category: 'AI产品', title: 'AI 产品评测方法', summary: '如何评估 AI 产品的质量与效果。', readMinutes: 9, updatedAt: '2026-08-26', status: '未开始' },
  { id: 9, category: '数据分析', title: 'AI 产品核心指标', summary: '准确率、采纳率、留存等 AI 产品指标。', readMinutes: 7, updatedAt: '2026-08-24', status: '未开始' },
]

export const knowledgeDetails = {
  1: {
    definition: '产品经理是负责定义产品方向、规划功能并推动落地的角色，是用户、业务与技术之间的连接者。',
    coreContent: ['发现并定义问题', '产出产品方案与优先级', '推动设计、开发、上线与迭代'],
    commonScenarios: ['需求评审会上澄清目标', '与研发沟通排期与取舍', '跟进版本上线后的数据反馈'],
    pmFocus: ['用户价值与商业价值的平衡', '需求优先级排序', '跨团队沟通与项目推进'],
    interviewQuestions: ['产品经理的一天通常是什么样的？', '如何理解产品经理的核心价值？'],
    referenceAnswers: ['围绕需求收集、方案设计、评审、跟进与复盘展开，核心是把机会转化为可落地的方案。', '把模糊的机会转化为可执行的产品方案，并推动落地产生价值。'],
  },
  2: {
    definition: '从需求到产品方案，是把用户/业务问题转化为可执行产品设计的过程，MVP 是最小验证手段。',
    coreContent: ['需求收集与筛选', '产品方案设计', 'PRD 撰写与 MVP 验证'],
    commonScenarios: ['新功能从想法到上线', '用最小成本验证一个假设', '撰写 PRD 对齐团队'],
    pmFocus: ['需求的真实性与优先级', '方案与目标的对齐', '用 MVP 快速验证核心假设'],
    interviewQuestions: ['拿到一个需求后，你的第一步是什么？', 'MVP 的边界如何确定？'],
    referenceAnswers: ['先澄清问题背景与目标，再结合用户调研判断需求真伪与优先级。', '只保留验证核心假设所必需的最小功能，其余留待验证后再迭代。'],
  },
  3: {
    definition: '核心数据指标与漏斗分析是衡量产品表现、定位问题的关键方法。',
    coreContent: ['北极星指标与关键指标', '漏斗分析', '留存与转化'],
    commonScenarios: ['设定北极星指标', '定位转化漏斗流失环节', '复盘留存变化'],
    pmFocus: ['选对指标而非看所有数据', '用数据验证假设', '定位流失环节'],
    interviewQuestions: ['如何为一个产品选择北极星指标？', '留存率下降你会怎么排查？'],
    referenceAnswers: ['围绕核心用户价值，选择可衡量、可行动且与业务目标一致的指标。', '按渠道、版本、用户分群拆解，定位流失环节再针对性验证。'],
  },
  4: {
    definition: 'AI 产品经理需要理解大模型能力边界，设计人机协作的产品体验。',
    coreContent: ['大模型能力与局限', 'AI 产品形态（对话 / 生成 / 助手）', '评估与迭代'],
    commonScenarios: ['判断场景是否适合大模型', '设计对话类产品的兜底策略', '处理模型幻觉'],
    pmFocus: ['识别适合 AI 的场景', '处理模型幻觉与不确定性', '设计反馈与兜底机制'],
    interviewQuestions: ['如何判断一个场景是否适合用大模型？', 'AI 产品如何应对回答不确定的问题？'],
    referenceAnswers: ['看任务是否高频、容错可控、能形成反馈闭环，以及是否有数据支撑。', '通过置信度、引用来源与兜底策略降低风险，并引导用户反馈。'],
  },
  5: {
    definition: '常用产品工具覆盖原型、文档、项目管理和协作，是 PM 的日常生产力。',
    coreContent: ['原型设计（Figma 等）', '文档协作', '项目管理与数据埋点'],
    commonScenarios: ['画原型', '写文档与协作', '埋点与数据分析'],
    pmFocus: ['工具为沟通与效率服务', '选择合适的工具组合', '沉淀可复用流程'],
    interviewQuestions: ['你常用的产品工具有哪些？', '工具选择的判断标准是什么？'],
    referenceAnswers: ['原型用 Figma、文档用 Notion、协作与项目管理视团队而定。', '以沟通效率和协作成本为判断标准，而非追求工具本身。'],
  },
  6: {
    definition: 'PM 面试高频问题覆盖自我介绍、项目复盘与开放题，考察思维与方法论。',
    coreContent: ['自我介绍与项目复盘', '开放题回答框架（如 STAR）', '常见产品设计题'],
    commonScenarios: ['自我介绍', '项目复盘', '开放题/设计题回答'],
    pmFocus: ['结构化表达', '体现产品思维而非背答案', '用数据与结果佐证'],
    interviewQuestions: ['请介绍一个你负责的项目。', '如何看待一个产品的失败？'],
    referenceAnswers: ['用 STAR 框架讲清背景、动作、结果与复盘，突出你的思考与产出。', '区分外部环境与内部决策，客观复盘并给出可复用的教训。'],
  },
  7: {
    definition: 'RAG（检索增强生成）是在大模型生成回答前，先从知识库检索相关内容作为上下文，从而提升准确性与可追溯性。',
    coreContent: ['文档切分与向量化', '检索与重排', '结合上下文生成回答'],
    commonScenarios: ['企业知识库问答', '客服机器人', '专业领域助手'],
    pmFocus: ['何时需要 RAG（知识时效性 / 专业领域）', '检索质量决定回答质量', '来源引用与可解释性'],
    interviewQuestions: ['RAG 能解决大模型的什么问题？', 'RAG 的主要局限是什么？'],
    referenceAnswers: ['缓解幻觉与知识时效性问题，让回答有据可依。', '依赖知识库质量、检索不准会误导回答，且引入额外延迟。'],
  },
  8: {
    definition: 'AI 产品评测是通过系统化的方法与指标，评估 AI 产品回答质量与用户体验的过程。',
    coreContent: ['评测集构建', '自动化指标与人工评估', 'A/B 与回归评测'],
    commonScenarios: ['评测集构建', '上线前质量把关', '版本迭代回归'],
    pmFocus: ['定义可衡量的质量标准', '平衡准确性与用户体验', '持续迭代评测体系'],
    interviewQuestions: ['如何评价一个 AI 助手的回答质量？', '自动化评测和人工评测如何配合？'],
    referenceAnswers: ['从相关性、正确性、有用性与安全性等维度综合评估。', '自动化指标做规模初筛，人工抽检做质量兜底与校准。'],
  },
  9: {
    definition: 'AI 产品核心指标用于衡量 AI 能力对业务与用户的实际价值。',
    coreContent: ['准确率 / 相关性', '采纳率与留存', '成本与延迟'],
    commonScenarios: ['衡量助手采纳率', '评估回答准确率', '控制成本与延迟'],
    pmFocus: ['指标要对应业务目标', '区分能力指标与业务指标', '平衡效果与成本'],
    interviewQuestions: ['AI 产品看哪些核心指标？', '回答准确率提升了，为什么留存没变？'],
    referenceAnswers: ['准确率、采纳率、留存率、成本与延迟等，视产品形态取舍。', '准确率不等于体验，还需关注是否真正解决用户问题与使用粘性。'],
  },
}

// ---- 学习 ----
export const qaPresets = [
  { q: '什么是 RAG？', a: 'RAG（检索增强生成）是在大模型生成回答前，先从知识库检索相关内容作为上下文，从而提升回答的准确性与可追溯性。', refs: ['RAG', 'Embedding'] },
  { q: '什么是 MVP？', a: 'MVP（最小可行产品）是用最少成本验证核心假设的版本，帮助快速获取真实反馈。', refs: ['产品基础', 'MVP'] },
]

export const learningPlanMeta = {
  title: 'AI 产品经理 14 天学习计划',
  currentDay: 4,
  totalDays: 14,
  todayTopic: '需求分析',
}

export const dailyTasks = [
  { id: 1, title: '阅读知识', done: true },
  { id: 2, title: '完成 AI 问答', done: false },
  { id: 3, title: '完成面试题', done: false },
]

// ---- 面试 ----
export const productDirections = ['C端产品经理', 'B端产品经理', 'AI产品经理', '数据产品经理']
export const difficultyLevels = ['基础', '中等', '困难']
export const interviewTypes = ['产品基础', '产品设计', '需求分析', 'AI产品', '综合面试']

export const mockSession = {
  direction: 'AI产品经理',
  difficulty: '中等',
}

export const mockQuestions = [
  { id: 1, text: '请简要介绍一款你常用的产品，并说明它解决了什么问题。', followUp: '如果让你改进它，你会先做哪一件事？' },
  { id: 2, text: '如何为一个新功能做优先级排序？', followUp: '如果资源只够做一件事，你会怎么选？' },
  { id: 3, text: '你如何看待 AI 对产品经理工作的影响？', followUp: '能否举一个具体场景说明？' },
  { id: 4, text: '谈谈你理解的产品经理的核心职责。', followUp: '与技术、设计协作时你会如何推进？' },
  { id: 5, text: '如何定义一个产品的北极星指标？', followUp: '如果指标下滑你会怎么排查？' },
  { id: 6, text: '什么是 RAG？它对 AI 产品有什么价值？', followUp: '它的主要局限是什么？' },
  { id: 7, text: '分享一个你参与过的项目，以及你的具体贡献。', followUp: '复盘时你觉得哪里可以做得更好？' },
  { id: 8, text: '如何判断一个需求是否值得做？', followUp: '如果被数据反驳，你会怎么处理？' },
]

export const mockReport = {
  id: 'sess-001',
  overall: 78,
  meta: { direction: 'AI产品经理', difficulty: '中等' },
  dimensions: [
    { name: '产品思维', score: 82 },
    { name: '需求分析', score: 80 },
    { name: '逻辑与表达', score: 78 },
    { name: 'AI知识', score: 65 },
    { name: '业务意识', score: 85 },
  ],
  strengths: ['用户分析', '需求拆解', '结构化表达'],
  weakPoints: ['RAG 理解', 'AI 产品指标', 'AI 评测'],
  recommendedKnowledge: [
    { id: 7, title: 'RAG 检索增强生成入门' },
    { id: 8, title: 'AI 产品评测方法' },
    { id: 9, title: 'AI 产品核心指标' },
  ],
}

// ---- 我的 ----
export const learningHistory = [
  { id: 1, title: '产品经理的核心职责', status: '已完成', date: '2026-09-12' },
  { id: 2, title: '从需求到产品方案与 MVP', status: '进行中', date: '2026-09-10' },
]

export const interviewHistory = [
  { id: 'sess-001', direction: 'AI产品经理', type: '产品设计', score: 82, date: '2026-09-14' },
  { id: 'sess-002', direction: 'C端产品经理', type: '产品基础', score: 75, date: '2026-09-11' },
]
